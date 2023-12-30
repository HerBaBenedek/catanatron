from collections import defaultdict
from typing import List, Literal, Final

from catanatron import Player
from catanatron_experimental.cli.cli_players import register_player
from catanatron.models.enums import *

@register_player("GT3")
class GameTheoryPlayerV3(Player):



    def __init__(self, color, is_bot=True, action_weights={}, base_weights={}, owned_resources={}):
       
        super().__init__(color, is_bot)
        self.action_weights = {
            ActionType.ROLL : 0,
            ActionType.MOVE_ROBBER : 0,
            ActionType.DISCARD : 0,
            ActionType.BUILD_ROAD : 10,
            ActionType.BUILD_SETTLEMENT : 20,
            ActionType.BUILD_CITY : 30,
            ActionType.BUY_DEVELOPMENT_CARD : 9,
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

        self.reset_state()

        self.debug_mode = False

    def reset_state(self):

        self.owned_resources = {
            WHEAT: 0,
            ORE: 0,
            BRICK: 0,
            WOOD: 0,
            SHEEP: 0
        }

        self.player_state = {
            "TOTAL": 0,
            "WHEAT": 0,
            "ORE": 0,
            "BRICK": 0,
            "WOOD": 0,
            "SHEEP": 0,
            "PREFIX": "",
            "SETTLEMENTS": 0,
            "CITIES": 0
        }

    def decide(self, game, playable_actions):
        """Should return one of the playable_actions.

        Args:
            game (Game): complete game state. read-only.
            playable_actions (Iterable[Action]): options to choose from
        Return:
            action (Action): Chosen element of playable_actions
        """

        self.debug("\n")
        self.write_game_state(game)

        self.calculate_player_state(game)

        best_action_value = 0

        best_action = playable_actions[0]

        updated_weights = self.update_weights()

        for action in playable_actions:
            
            current_action_value = self.calculate_action_weights(game, action, updated_weights)

            if current_action_value > best_action_value:
                best_action_value = current_action_value
                best_action = action

        if best_action.action_type == ActionType.BUILD_SETTLEMENT or best_action.action_type == ActionType.BUILD_CITY:

            self.update_owned_resources(game, game.state.board.map.adjacent_tiles[best_action.value])

        if best_action.action_type == ActionType.BUILD_SETTLEMENT:

            self.player_state["SETTLEMENTS"] += 1

        if best_action.action_type == ActionType.BUILD_CITY:

            self.player_state["CITIES"] += 1
            self.player_state["SETTLEMENTS"] -= 1

        self.debug(f"Chosen Action: {best_action.action_type} {best_action.value} {best_action_value}\nOwned Resources: {self.owned_resources}")

        return best_action

    def calculate_action_weights(self, game, action, updated_weights):

        weight = self.action_weights[action.action_type]

        if action.action_type == ActionType.BUILD_SETTLEMENT:

            weight += self.calculate_node_value(game, game.state.board.map.adjacent_tiles[action.value], updated_weights) 

        if action.action_type == ActionType.BUILD_CITY:

            weight += self.calculate_node_value(game, game.state.board.map.adjacent_tiles[action.value], updated_weights) * 2

        if action.action_type == ActionType.BUY_DEVELOPMENT_CARD:

            if self.player_state["TOTAL"] <= 7:
                
                if self.distance_to_city() < 2 and self.player_state["CITIES"] < 4 and self.player_state["SETTLEMENTS"] > 0:

                    weight = 0

                elif self.distance_to_settlement() < 2 and self.player_state["SETTLEMENTS"] < 5: 

                    weight = 0

        self.debug(f"{action.action_type}: {weight}")

        return weight

    def update_weights(self):
        """Args:
            owned_resources: dict of all owned tiles by resource type"""

        updated_weights = {}

        self.debug(f"Owned Resources: {self.owned_resources}")

        for resource in self.owned_resources:
            updated_weights[resource] = self.base_weights[resource] / 2**self.owned_resources[resource]
        
        self.debug(f"Updated Weights: {updated_weights}")

        return updated_weights 

    def calculate_node_value(self, game, tiles, updated_weights):

        node_value = 0        

        for tile in tiles:

            if tile.resource != None:
            
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
        
    def update_owned_resources(self, game, tiles):

        for tile in tiles:

            if tile.resource != None:
            
                self.owned_resources[tile.resource] += 1

    def debug(self, message):

        if self.debug_mode:

            print(message)

    def write_game_state(self, game):

        player_index = game.state.color_to_index[self.color]

        prefix = f"P{player_index}_"

        self.debug(f"{game.state.num_turns}")
        self.debug(f"""Cards: 
            {game.state.player_state[prefix + "WHEAT_IN_HAND"]} Wheat 
            {game.state.player_state[prefix + "ORE_IN_HAND"]} Ore
            {game.state.player_state[prefix + "WOOD_IN_HAND"]} Wood
            {game.state.player_state[prefix + "BRICK_IN_HAND"]} Brick
            {game.state.player_state[prefix + "SHEEP_IN_HAND"]} Sheep"""
        )

    def calculate_player_state(self, game):

        player_index = game.state.color_to_index[self.color]

        prefix = f"P{player_index}_"

        self.player_state["PREFIX"] = prefix

        total = 0

        for resource in RESOURCES:

            self.player_state[resource] = game.state.player_state[f"{prefix}{resource}_IN_HAND"]

            total += game.state.player_state[f"{prefix}{resource}_IN_HAND"]

        self.player_state["TOTAL"] = total

    def distance_to_city(self):

        return abs(3 - self.player_state["ORE"]) + abs(2 - self.player_state["WHEAT"])

    def distance_to_settlement(self):

        return abs(1 - self.player_state["SHEEP"]) + abs(1 - self.player_state["WHEAT"]) + abs(1 - self.player_state["WOOD"]) + abs(1 - self.player_state["BRICK"])
