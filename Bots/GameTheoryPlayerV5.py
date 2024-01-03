from collections import defaultdict, OrderedDict
from typing import List, Literal, Final, Union

from catanatron import Player
from catanatron_experimental.cli.cli_players import register_player
from catanatron.models.enums import *
from catanatron.models.board import STATIC_GRAPH, get_edges

@register_player("GT5")
class GameTheoryPlayerV5(Player):



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
            ActionType.MARITIME_TRADE : 5,
            ActionType.OFFER_TRADE : 0,
            ActionType.ACCEPT_TRADE : 0,
            ActionType.REJECT_TRADE : 0,
            ActionType.CONFIRM_TRADE : 0,
            ActionType.CANCEL_TRADE : 0,
            ActionType.END_TURN : 4  }
        
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

        self.decisions = {
            "CITIES": 0,
            "SETTLEMENTS": 0,
            "ROADS": 0,
            "DEVELOPEMENT_CARDS": 0,
            "MARITIME_TRADES": 0
        }

        self.actions = {}

        self.owned_nodes = []

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
            self.owned_nodes.append(best_action.value)


        if best_action.action_type == ActionType.BUILD_CITY:

            self.player_state["CITIES"] += 1
            self.player_state["SETTLEMENTS"] -= 1
            self.owned_nodes.append(best_action.value)

        self.update_actions(best_action)

        self.debug(f"Chosen Action: {best_action.action_type} {best_action.value} {best_action_value}\nOwned Resources: {self.owned_resources}")

        return best_action

    def calculate_action_weights(self, game, action, updated_weights):

        weight = self.action_weights[action.action_type]

        if action.action_type == ActionType.BUILD_SETTLEMENT:

            weight += self.calculate_node_value(game, action.value, updated_weights) 

            self.decisions["SETTLEMENTS"] += 1

        if action.action_type == ActionType.BUILD_CITY:

            weight += self.calculate_node_value(game, action.value, updated_weights) * 2

            self.decisions["CITIES"] += 1

        if action.action_type == ActionType.BUY_DEVELOPMENT_CARD:

            if self.player_state["TOTAL"] <= 7:
                
                if self.distance_to_city() < 2 and self.player_state["CITIES"] < 4 and self.player_state["SETTLEMENTS"] > 0:

                    weight = 0

                elif self.distance_to_settlement() < 2 and self.player_state["SETTLEMENTS"] < 5: 

                    weight = 0

            self.decisions["DEVELOPEMENT_CARDS"] += 1

        if action.action_type == ActionType.MARITIME_TRADE:

            weight = self.maritime_trade(game, action, updated_weights, weight)

        if action.action_type == ActionType.MOVE_ROBBER:

            weight = self.move_robber(game, action, updated_weights)

        if action.action_type == ActionType.BUILD_ROAD:

            weight = self.build_road(game, action, updated_weights, weight)

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

    def calculate_node_value(self, game, node_id, updated_weights):

        tiles = game.state.board.map.adjacent_tiles[node_id]
        
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

    def game_over(self):

        print(self.owned_resources)
        print(self.decisions)
        print(self.actions)
        print(self.owned_nodes)

    def update_actions(self, best_action):

        if best_action.action_type.name in self.actions:

            self.actions[best_action.action_type.name] += 1

        else:

            self.actions[best_action.action_type.name] = 1
            
    def move_robber(self, game, action, updated_weights):

        tile = game.state.board.map.land_tiles[action.value[0]]

        if action.value[1] == None or tile.resource == None:

                weight = 0

        else:

            player_id = game.state.color_to_index[action.value[1]]

            weight = game.state.player_state[f"P{player_id}_VICTORY_POINTS"] + updated_weights[tile.resource] * self.number_probability(tile.number)

        return weight

    def maritime_trade(self, game, action, updated_weights, weight):

        trade_resources_weight = 0

        resource_num = 0

        for resource in action.value:

            resource_num += 1

            if resource != None:

                if resource_num < 5:

                    trade_resources_weight -= updated_weights[resource]

                else:

                    trade_resources_weight += updated_weights[resource]

        if trade_resources_weight > 0:

            weight += trade_resources_weight

        elif self.player_state["TOTAL"] > 7:

            weight += trade_resources_weight

        else:

            weight = 0
           
        self.decisions["MARITIME_TRADES"] += 1

        return weight

    def build_road(self, game, action, updated_weights, weight):

        edge_weights = self.calculate_edge_weights(game, updated_weights)

        if action.value in edge_weights.keys():

            weight += edge_weights[action.value]

        else:

            weight = 0

        self.decisions["ROADS"] += 1
        
        return weight

    def calculate_edge_weights(self, game, updated_weights):

        buildable_nodes = game.state.board.board_buildable_ids

        edge_weights = {}

        edges = get_edges()

        available_edges = []

        base_nodes = OrderedDict()

        distance_limit = 3

        for node in self.owned_nodes:

            base_nodes[node] = (0, [], 1)

        for edge in edges:

            edge_color = game.state.board.get_edge_color(edge)

            if edge_color == None or edge_color == self.color:

                available_edges.append(edge)

        while len(base_nodes) > 0:

            node_id, node_info = base_nodes.popitem(False)

            if node_info[0] > distance_limit and edge_weights != {}:

                break

            elif node_info[0] > distance_limit: 

                distance_limit += 1

            for edge in available_edges:

                other_node = -1

                if node_id == edge[0]:

                    other_node = edge[1]

                elif node_id == edge[1]:

                    other_node = edge[0]
                
                if other_node != -1 and other_node not in base_nodes.keys():

                    actual_distance = node_info[2]

                    if game.state.board.get_edge_color(edge) == None:

                        actual_distance += 1

                    base_nodes[other_node] = (node_info[0] + 1, node_info[1] + [edge], actual_distance)

                    if other_node in buildable_nodes:

                        node_weight = self.calculate_node_value(game, other_node, updated_weights)

                        for road in base_nodes[other_node][1]:

                            road_weight = node_weight / base_nodes[other_node][2]

                            if road not in edge_weights.keys() or road_weight > edge_weights[road]:

                                edge_weights[road] = road_weight

        self.debug(f"Buildable Nodes:{buildable_nodes}")
        self.debug(f"Available Edges: {available_edges}")
        self.debug(f"Edge Weights: {edge_weights}")

        return edge_weights