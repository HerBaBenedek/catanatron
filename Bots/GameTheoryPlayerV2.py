from collections import defaultdict

from catanatron import Player
from catanatron_experimental.cli.cli_players import register_player
from catanatron.models.enums import *

@register_player("GT2")
class GameTheoryPlayerV2(Player):



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
            SHEEP: 0.760,
            None: 0
        }

    def reset_state(self):

        self.owned_resources = {
            WHEAT: 0,
            ORE: 0,
            BRICK: 0,
            WOOD: 0,
            SHEEP: 0
        }

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

        best_action_value = 0

        best_action = playable_actions[0]

        updated_weights = self.base_weights

        for action in playable_actions:
            
            current_action_value = self.calculate_action_weights(game, action, updated_weights)

            if current_action_value > best_action_value:
                best_action_value = current_action_value
                best_action = action

        if best_action.action_type == ActionType.BUILD_SETTLEMENT or best_action.action_type == ActionType.BUILD_CITY:

            pass

        """print(f"Chosen Action: {best_action} {best_action_value}")"""

        return best_action

    def calculate_action_weights(self, game, action, updated_weights):

        weight = self.action_weights[action.action_type]

        if action.action_type == ActionType.BUILD_SETTLEMENT:

            weight = 20 + self.calculate_node_value(game, game.state.board.map.adjacent_tiles[action.value], updated_weights) 

        if action.action_type == ActionType.BUILD_CITY:

            weight = 30 + self.calculate_node_value(game, game.state.board.map.adjacent_tiles[action.value], updated_weights) * 2

        """print(f"{action.action_type}: {weight}")"""

        return weight

    def update_weights(self, owned_resources):
        """Args:
            owned_resources: dict of all owned tiles by resource type"""

        updated_weights = self.base_weights

        for resource, count in owned_resources:
            updated_weights[resource] = self.base_weights / 2**count

        """print (f"base weights: {self.base_weights}")
        print (f"updated weights: {updated_weights}")"""

        return updated_weights 

    def calculate_node_value(self, game, tiles, updated_weights):

        node_value = 0

        for tile in tiles:

            node_value += updated_weights[tile.resource] * self.number_probability(tile.number)

        return node_value

    def build_dice_probas():
        probas = defaultdict(float)
        for i in range(1, 7):
            for j in range(1, 7):
                probas[i + j] += 1
        return probas

    DICE_PROBAS = build_dice_probas()

    def number_probability(self, number):
        return self.DICE_PROBAS[number]
        