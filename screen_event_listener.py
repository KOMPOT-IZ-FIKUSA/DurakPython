import os

import cv2

import utils
import events

class ScreenEventListener:
    def __init__(self):
        self.log = []

    def handle_frame(self, game_img):


        cv2.imshow("w", game_img)
        key = cv2.waitKey(1)

        if len(self.log) == 0:
            if utils.is_in_game_scene(game_img):
                daws = utils.get_readiness_daws_positions(game_img)
                all_enemies_are_ready = utils.do_daws_positions_match_to_icons_template(daws)
                if all_enemies_are_ready:
                    if utils.is_self_player_ready_or_plaiyng(game_img):
                        properties = utils.get_game_properties(game_img, len(daws))
                        print(properties)
                        self.log.append(event.GameStart(properties))

