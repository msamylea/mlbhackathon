import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from constants import team_mapping
from utils.custom_serializer import serialize_game_object_to_dict
from services.game_statistics_summary import GameStatsManager
from sim.historical_simulator import HistoricalMatchupSimulator
from data.mlb_client import MLBDataClient
from events.game_events import EventManager
from data.data_loader import TeamDataLoader
from stats.centralized_stats import CentralizedStatsService
from utils.gemini_config import get_llm
from datetime import datetime

import os



app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   ping_timeout=10,
                   ping_interval=5)


def initialize_components():
    """Initialize all game components with dependencies"""
    try:
        mlb_client = MLBDataClient()
        team_data_loader = TeamDataLoader()
        stats_service = CentralizedStatsService()
        event_manager = EventManager()
        
        return {
            'mlb_client': mlb_client,
            'stats_service': stats_service,
            'event_manager': event_manager,
            'team_data_loader': team_data_loader,
        }
    except Exception as e:
        raise

@socketio.on('set_api_key')
def handle_api_key(api_key):
    session['api_key'] = api_key
    emit('api_key_set', {'message': 'API key set successfully'})


@app.route('/api/teams')
def get_teams():
    """Return all teams from team mapping excluding All-Star teams"""
    teams = {id: name for id, name in team_mapping.items() if "All-Stars" not in name}
    return jsonify(teams)

@app.route('/api/team_details/<team_id>')
def get_team_details(team_id):
    try:
        year = request.args.get('season')
        
        if not year:
            year = datetime.now().year
        else:
            try:
                year = int(year)
            except ValueError:
                return jsonify({'error': f'Invalid year format: {year}'}), 400
        
        try:
            team_id = int(team_id)
        except ValueError:
            return jsonify({'error': f'Invalid team ID format: {team_id}'}), 400
            
        team_data = team_data_loader.get_team_details(team_id, year)
        
        team_info = team_data['teams'][0]
        
        valid_year = int(team_info['firstYearOfPlay']) <= year <= datetime.now().year
        if not valid_year:
            return jsonify({'error': 'Invalid year for team'}), 400
        
        return jsonify({
            'years': list(range(int(team_info['firstYearOfPlay']), datetime.now().year + 1)),
            'details': {
                'id': team_id,
                'name': team_info['name'],
                'firstYearOfPlay': team_info['firstYearOfPlay'],
                'venue': team_info['venue']['name'],
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate_api_key', methods=['POST'])
def validate_api_key():
    api_key = request.json.get('api_key')
    model = request.json.get('llm_model')
    if not api_key:
        return jsonify({'valid': False, 'message': 'No API key provided'})
    
    try:
        test_config = {
            'provider': 'google',
            'model': model,
            'api_key': api_key
        }
        test_llm = get_llm(**test_config)
        # Simple test generation
        test_llm.get_response("test")
        return jsonify({'valid': True, 'model': model})
    except Exception as e:
        error_msg = str(e)
        if 'API_KEY_INVALID' in error_msg or 'INVALID_ARGUMENT' in error_msg:
            return jsonify({'valid': False, 'message': 'Invalid Google Gemini API key'})
        if 'model is required' in error_msg:
            return jsonify({'valid': False, 'message': 'Model is required'})
        return jsonify({'valid': False, 'message': 'Error connecting to Gemini API'})

    
@socketio.on('start_game')
def handle_game_simulation(data):
    try:
        api_key = data['api_key']
        model = data['model']
        llm_config = {
            'provider': 'google',
            'model': model,
            'api_key': api_key
        }

        simulator = HistoricalMatchupSimulator()
        simulator.game_simulator.client = get_llm(**llm_config)
        game_stats_manager = GameStatsManager(home_team=data['home_team'], away_team=data['away_team'])
        game_stats_manager.client = get_llm(**llm_config)

        global home_team_id, away_team_id
        # Get team IDs
        home_team_id = next((id for id, name in team_mapping.items() 
                       if data['home_team'] in name), None)
        away_team_id = next((id for id, name in team_mapping.items() 
                       if data['away_team'] in name), None)

        global home_team_name, away_team_name
        home_team_name = data['home_team']
        
        away_team_name = data['away_team']
                              
        if not home_team_id or not away_team_id:
            raise ValueError("Invalid team selection")

        global home_year, away_year
        home_year = data['home_year']
        away_year = data['away_year']

        def send_play_to_frontend(play_data):
            try:
                
                play_data['play_details']['away_team_id'] = away_team_id
                play_data['play_details']['home_team_id'] = home_team_id
                
                play_data['play_details']['home_team_name'] = home_team_name
                play_data['play_details']['away_team_name'] = away_team_name
                play_data['play_details']['year1'] = away_year
                play_data['play_details']['year2'] = home_year

                if hasattr(play_data['play_details']['base_state'], 'to_list'):
                    play_data['play_details']['base_state'] = play_data['play_details']['base_state'].to_list()
                elif isinstance(play_data['play_details']['base_state'], str):
                    play_data['play_details']['base_state'] = play_data['play_details']['base_state'].split(', ')

                              
                serialized_data = serialize_game_object_to_dict(play_data)
                socketio.emit('play_result', serialized_data)
                
            except Exception as e:
                socketio.emit('game_error', {'message': str(e)})
                raise ValueError(f"Error sending play to frontend: {str(e)}")
                        
        def send_game_over(end_data):
            socketio.emit('game_status', {
                'message': 'Game Over',
                'type': 'end',
                'final_score': end_data['final_score'],
                'innings': end_data['innings'],
                'game_summary': end_data['game_summary'],
                'llm_analysis': end_data['llm_analysis']
            })

        simulator.event_manager.subscribe('play_result', send_play_to_frontend)
        simulator.event_manager.subscribe('game_status', send_game_over)
        
        result, stats_details = simulator.simulate_matchup(
            team1_id=int(away_team_id),
            year1=away_year,
            team2_id=int(home_team_id),
            year2=home_year,
            team1_name=away_team_name,
            team2_name=home_team_name
        )

    except Exception as e:
        error_msg = f"Game error: {str(e)}"
        socketio.emit('game_error', {
            'message': error_msg,
            'type': 'error'
        })
        
        
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Initialize components
    try:
        components = initialize_components()
        mlb_client = components['mlb_client']
        event_manager = components['event_manager']
        team_data_loader = components['team_data_loader']
    except Exception as e:
        raise ValueError(f"Failed to initialize components: {e}")

    # Run the server
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, 
                host='0.0.0.0', 
                port=port,
                debug=True,
                use_reloader=True)