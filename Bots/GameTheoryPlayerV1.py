from catanatron import Player
from catanatron_experimental.cli.cli_players import register_player
from catanatron.models.enums import *

@register_player("GT1")
class GameTheoryPlayerV1(Player):



    def __init__(self, color, is_bot=True, action_weights={}, base_weights={}, node_values={}):
       
        super().__init__(color, is_bot)
        self.action_weights = {
            ActionType.ROLL : 0,
            ActionType.MOVE_ROBBER : 0,
            ActionType.DISCARD : 0,
            ActionType.BUILD_ROAD : 10,
            ActionType.BUILD_SETTLEMENT : 20,
            ActionType.BUILD_CITY : 30,
            ActionType.BUY_DEVELOPMENT_CARD : 10,
            ActionType.PLAY_KNIGHT_CARD : 10,
            ActionType.PLAY_YEAR_OF_PLENTY : 10,
            ActionType.PLAY_MONOPOLY : 10,
            ActionType.PLAY_ROAD_BUILDING : 10,
            ActionType.MARITIME_TRADE : 0,
            ActionType.OFFER_TRADE : 0,
            ActionType.ACCEPT_TRADE : 0,
            ActionType.REJECT_TRADE : 0,
            ActionType.CONFIRM_TRADE : 0,
            ActionType.CANCEL_TRADE : 0,
            ActionType.END_TURN : 5  }
        
        self.base_weights = {
            WHEAT: 1.350,
            ORE: 1.329,
            BRICK: 0.781,
            WOOD: 0.781,
            SHEEP: 0.760
        }

        self.node_values = {}

    def decide(self, game, playable_actions):
        """Should return one of the playable_actions.

        Args:
            game (Game): complete game state. read-only.
            playable_actions (Iterable[Action]): options to choose from
        Return:
            action (Action): Chosen element of playable_actions
        """
        """print("\n")
        print(playable_actions)"""

        if len(self.node_values) == 0:
            self.calculate_node_values(game)
        
        if len(playable_actions) == 1:
            return playable_actions[0]

        best_action_value = 0

        best_action = playable_actions[0]

        for action in playable_actions:
            
            current_action_value = self.action_weights[action.action_type]

            if current_action_value > best_action_value:
                best_action_value = current_action_value
                best_action = action

        return best_action

    def calculate_node_values(self, game):
        print("X")

