import numpy as np


wdith = 512
height = 1024
gamefield_y = 228
gamefield_height = 480
cards_ranges = (np.array([240, 240, 240]), np.array([255, 255, 255]))
player_red_frames_ranges = (np.array([31, 80, 127]), np.array([73, 255, 255]))


ranks_string_to_value = {str(i): i for i in range(2, 11)}
ranks_string_to_value.update({"J": 11, "Q": 12, "K": 13, "A": 14})
ranks_value_to_string = {v: k for k, v in ranks_string_to_value.items()}

suits = "♠♥♣♦"
red_suits_indices = (1, 3)
suit_names = {"♠": "Пики", "♥": "Черви", "♣": "Крести", "♦": "Бубны"}

suit_names_for_java = {"♠": "PIKI", "♥": "CHERVI", "♣": "KRESTI", "♦": "BUBNY"}

stable_frame_threshold = 1

readiness_daw_threshold = 0.9

right_down_corner_in_game_scene_threshold = 0.05
left_corner_player_ready_threshold = 0.05
game_properties_rect = (143, 47, 201, 51)
speed_rule_threshold = 0.95

deck_cards_count_rect = (4, 308, 48, 32)
window_search_y_ranges = ((0, 50), (980, 1080))

deck_digit_color_ranges = (np.array([220, 220, 220]), np.array([255, 255, 255]))
deck_digit_threshold = 0.78

player_icons_centers = {
    3: [(146, 140), (337, 142)],
    4: [(49, 151), (242, 130), (434, 150)]
}
icons_template_match_distance_threshold = 40
from_daw_to_icon_center_distance = (19, 43)

bet_right_up_rect = (369, 34, 121, 38)
bet_threshold = 0.97

modes_phrases = {
    0: "пас",
    1: "атакующий, покрыто",
    2: "атакующий, не покрыто",
    3: "unknown",
    4: "бито",
    5: "unknown",
    6: "ход заблокирован",
    7: "принял",
    8: "кроется, покрыто",
    9: "кроется, не покрыто",
}
SERVER_IP = "cc:32:e5:33:58:e8"

max_time_between_hand_and_order_event = 2