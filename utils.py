import os
import time

import cv2
import numpy as np
import pyautogui as pag

# def save_screenshot():
#
import const
import game_properties


def screenshot():
    return np.array(pag.screenshot())

def crop(image_yx, rect_xywh):
    return image_yx[rect_xywh[1]:rect_xywh[1]+rect_xywh[3], rect_xywh[0]:rect_xywh[0]+rect_xywh[2]]

bluestacks_icon = cv2.cvtColor(cv2.imread("data/png_to_locate/bluestacks_icon.png"), cv2.COLOR_BGR2RGB)
bluestacks_right_down_corner = cv2.cvtColor(cv2.imread("data/png_to_locate/bluestacks_right_down_corner_32.png"), cv2.COLOR_BGR2RGB)
def get_bluestacks_rect(screen):
    r = const.window_search_y_ranges
    res = cv2.matchTemplate(screen[r[0][0]:r[0][1]], bluestacks_icon, cv2.TM_CCOEFF_NORMED)
    index = np.unravel_index(np.argmax(res, axis=None), res.shape)
    x0 = index[1]
    y0 = index[0]

    res = cv2.matchTemplate(screen[r[1][0]:r[1][1]], bluestacks_right_down_corner, cv2.TM_CCOEFF_NORMED)
    index = np.unravel_index(np.argmax(res, axis=None), res.shape)
    x1 = index[1] + bluestacks_right_down_corner.shape[1]
    y1 = index[0] + bluestacks_right_down_corner.shape[0]
    y1 += r[1][0]

    if 400 < x1-x0 < 600 and 900 < y1-y0 < 1100:
        return x0, y0, x1-x0, y1-y0
    else:
        return None

def get_img(screen_img):
    rect = get_bluestacks_rect(screen_img)
    if rect:
        img = crop(screen_img, rect)
        img = cv2.resize(img, (const.wdith, const.height))
        return img
    else:
        return None

def save_test_screenshot():
    img = screenshot()
    rect = get_bluestacks_rect(img)
    img = crop(img, rect)
    img = cv2.resize(img, (const.wdith, const.height))
    path = f"data/test_screenshots/"
    path += str(len(os.listdir(path))) + ".jpg"
    cv2.imwrite(path, img)

def crop_gamefield(game_img):
    return game_img[const.gamefield_y:const.gamefield_y+const.gamefield_height]

def get_cards_rects(gamefield):
    mask = cv2.inRange(gamefield, *const.cards_ranges)
    contours, _ = cv2.findContours(mask.copy(), 1, 1)
    alpha = 8/9
    for contour in contours:
        rect = cv2.boundingRect(contour)
        if rect[2] * rect[3] < 13000:
            continue
        contour = np.concatenate((contour, np.array([[[int(rect[0] + rect[2]*alpha), int(rect[1]+rect[3]*alpha)]]])), axis=0)
        rect1 = cv2.minAreaRect(contour)  # basically you can feed this rect into your classifier
        box = cv2.boxPoints(rect1)
        box = np.int0(box)
        cv2.drawContours(gamefield, [box], -1, (0, 255, 0), 2)
    cv2.imshow("w", gamefield)
    cv2.waitKey(0)

#cv2.namedWindow("1")
#cv2.createTrackbar("hue max", "1", 255, 255, int)
#cv2.createTrackbar("sat max", "1", 255, 255, int)
#cv2.createTrackbar("val max", "1", 255, 255, int)
#
#cv2.createTrackbar("hue min", "1", 0, 255, int)
#cv2.createTrackbar("sat min", "1", 0, 255, int)
#cv2.createTrackbar("val min", "1", 0, 255, int)



def get_red_frames_positions(game_img):

    #const.player_red_frames_ranges[0][0] = cv2.getTrackbarPos("hue min", "1")
    #const.player_red_frames_ranges[0][1] = cv2.getTrackbarPos("sat min", "1")
    #const.player_red_frames_ranges[0][2] = cv2.getTrackbarPos("val min", "1")
    #const.player_red_frames_ranges[1][0] = cv2.getTrackbarPos("hue max", "1")
    #const.player_red_frames_ranges[1][1] = cv2.getTrackbarPos("sat max", "1")
    #const.player_red_frames_ranges[1][2] = cv2.getTrackbarPos("val max", "1")


    game_img = game_img[85:200]
    game_img = cv2.cvtColor(game_img, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(game_img, *const.player_red_frames_ranges)
    cv2.imshow("w1", mask)
    contours, _ = cv2.findContours(mask.copy(), 1, 1)
    positions = []
    for c in contours:
        rect = cv2.boundingRect(c)
        if 3000 < rect[2] * rect[3] < 6000:
            positions.append((rect[0] + rect[2]//2, rect[1] + rect[3]//2))
    filter_list_of_coordinates_by_x_distance(positions, 50)
    return positions

#def action_index(prev_frame, current_frame):
#    return np.average((prev_frame - current_frame)**2)

def extract_cards_pairs(game_field, rets):
    pass

def filter_list_of_coordinates_by_x_distance(lst, min_distance):
    if len(lst) == 1:
        return
    lst.sort(key=lambda xy: xy[0])
    i = len(lst) - 2
    while i >= 0:
        if abs(lst[i+1][0] - lst[i][0]) < min_distance:
            lst.pop(i)
        i -= 1

readiness_daw = cv2.imread("data/png_to_locate/readiness_daw.png")
def get_readiness_daws_positions(game_img):
    res = cv2.matchTemplate(game_img[:300], readiness_daw, cv2.TM_CCOEFF_NORMED)
    res[res < const.readiness_daw_threshold] = 0
    indices = np.where(res > const.readiness_daw_threshold)
    if len(indices) == 0:
        return []
    indices = list(zip(indices[1], indices[0]))  # change x to y and stack
    filter_list_of_coordinates_by_x_distance(indices, 20)
    delta = const.from_daw_to_icon_center_distance
    indices = [[x + delta[0], y + delta[1]] for x, y in indices]
    return indices

right_down_corner_in_game_scene = cv2.imread("data/png_to_locate/right_down_corner_in_game_scene.png")
def is_in_game_scene(game_img):
    cropped = game_img[-right_down_corner_in_game_scene.shape[0]:, -right_down_corner_in_game_scene.shape[1]:]
    difference = np.average(np.abs(cropped.astype(np.int32) - right_down_corner_in_game_scene)) / 255
    return difference < const.right_down_corner_in_game_scene_threshold

player_ready_left_down_corner = cv2.imread("data/png_to_locate/player_ready_left_down_corner.png")
def is_self_player_ready_or_plaiyng(game_img):
    cropped = game_img[-player_ready_left_down_corner.shape[0]:, :player_ready_left_down_corner.shape[1]]
    difference = np.average(np.abs(cropped.astype(np.int32) - player_ready_left_down_corner)) / 255
    return difference < const.left_corner_player_ready_threshold

def _read(names):
    return [cv2.imread(os.path.join("data/png_to_locate", name + ".png")) for name in names]

redirect_rule_names = ("redirect_rule", "no_redirects_rule")
redirect_rule_images = _read(redirect_rule_names)
secondary_attack_rules = ("sides_secondary_attack_rule", "all_secondary_attack_rule")
secondary_attack_rules_images = _read(secondary_attack_rules)
shapers_rules = ("with_shapers_rule", "without_shapers_rule")
shapers_rules_images = _read(shapers_rules)
draws_rules = ("with_draws_rule", "no_draws_rule")
draws_rules_images = _read(draws_rules)
speed_rule_image = cv2.cvtColor(cv2.imread("data/png_to_locate/speed_rule.png"), cv2.COLOR_BGR2RGB)


digits = [cv2.imread(f"data/digits/{i}.png")[:, :, 0] for i in range(10)]
def get_deck_cards_count(game_img):
    cropped = crop(game_img, const.deck_cards_count_rect)
    cropped_mask = cv2.inRange(cropped, *const.deck_digit_color_ranges)
    res_digits = []
    for digit in range(10):
        mask = cv2.matchTemplate(cropped_mask, digits[digit], cv2.TM_CCOEFF_NORMED)
        indices = np.where(mask > const.deck_digit_threshold)
        indices = list(zip(*indices))
        filter_list_of_coordinates_by_x_distance(indices, 5)
        if len(indices) == 2:
            return digit * 11
        elif len(indices) == 1:
            res_digits.append((indices[0][1], digit))  # x, d
            if len(res_digits) == 2:
                break
    if res_digits[0][0] < res_digits[1][0]:
        return res_digits[0][1] * 10 + res_digits[1][1]
    else:
        return res_digits[1][1] * 10 + res_digits[0][1]



def _max_match(img, template):
    return np.max(cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED))

def _does_first_match_better(img, first, second):
    print(_max_match(img, first), _max_match(img, second))
    return _max_match(img, first) > _max_match(img, second)

def get_game_properties(game_img, players_count):
    cropped = crop(game_img, const.game_properties_rect)
    f = lambda tuple_: _does_first_match_better(cropped, *tuple_)
    cards_count = get_deck_cards_count(game_img)
    return game_properties.GameProperties(
        redirect=f(redirect_rule_images),
        secondary_attack_sides_only=f(secondary_attack_rules_images),
        shapers=f(shapers_rules_images),
        draw=f(draws_rules_images),
        speed=_max_match(cropped, speed_rule_image) > const.speed_rule_threshold,
        players_count=players_count,
        lowest_card_rank=15 - cards_count // 4,
        bet=get_bet(game_img)
    )

def do_daws_positions_match_to_icons_template(daws):
    l = len(daws) + 1
    if const.player_icons_centers.get(l) is None:
        return False
    daws.sort(key=lambda pos: pos[0])
    avg_distance = 0
    for daw_pos, template_pos in zip(daws, const.player_icons_centers[l]):
        distance = ((daw_pos[0] - template_pos[0])**2 + (daw_pos[1] - template_pos[1])**2)**0.5
        avg_distance += distance
    avg_distance // len(daws)
    return avg_distance < const.icons_template_match_distance_threshold


bet_images = {int(filename[:-4]): cv2.imread(f"data/bet/{filename}").astype(np.int32) for filename in os.listdir("data/bet/")}
def get_bet(game_img):
    cropped = crop(game_img, const.bet_right_up_rect)
    max_conj = 0
    max_conj_bet = 0
    for bet, bet_image in bet_images.items():
        conjunction = 1 - np.average(np.abs(bet_image - cropped)) / 255
        if conjunction > max_conj:
            max_conj = conjunction
            max_conj_bet = bet
    if max_conj > const.bet_threshold:
        return max_conj_bet
    else:
        return None