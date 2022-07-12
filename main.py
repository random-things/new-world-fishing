import math
import time
import keyboard
import json
import logging

from NewWorldScreenshot import NewWorldScreenshot
from Player import Player, PlayerState

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                    level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')

logging.debug('Started!')

should_stop = False

with open('markers.json') as f:
    markers = json.load(f)


def stop_bot():
    global should_stop
    logging.debug("Stop combination pressed.")
    should_stop = True


def main():
    keyboard.add_hotkey('ctrl+alt+s', stop_bot)

    loop = True
    last_position = None
    last_ocr_position = None
    point_index = 0
    player = Player()
    player.maintain_bearing = None
    new_world = NewWorldScreenshot()

    while not should_stop:
        logging.debug(f"Starting loop")

        if player.is_moving():
            logging.debug(f"Already moving, skipping this round")
            time.sleep(0.1)
            continue

        new_world.take(title="New World", bring_to_front=True)

        # region fishing
        # Check to see if we're fishing
        boxes = new_world.find_template(template='fish_hooked')
        if boxes:
            player.update_state(PlayerState.FISHING_CAN_SINK)
            continue

        boxes = new_world.find_template(template='fishing_ready')
        if boxes:
            # Wait to cast
            player.update_state(PlayerState.FISHING_CAN_CAST)
            continue

        boxes = new_world.find_template(template='fish_unhooked')
        if boxes:
            # Wait to hook a fish
            player.update_state(PlayerState.FISHING_WAITING)
            continue

        boxes = new_world.find_template(template='fish_reeling')
        if boxes:
            # Reel it in
            player.update_state(PlayerState.FISHING_CAN_REEL)
            continue

        player.update_bearing(new_world.get_bearing())
        time.sleep(.1)
        continue
        # endregion

        position = new_world.get_position()
        logging.debug(f"Position: {position}")

        if position and position[0] is not None:
            if last_position:
                # Calculate the last spot we were and where we are now.
                maximum_distance = (time.time() - player.last_move_time) * 5  # 5m/s is the approximate running limit.

                if player.distance_from(position[0], position[1]) > maximum_distance:
                    if last_ocr_position:
                        if distance(position[0], position[1], last_ocr_position[0], last_ocr_position[1]) > maximum_distance:
                            # Our last position is wrong and the last OCR position is right.
                            last_position = last_ocr_position
                    # We've moved pretty far, teleport or bad OCR.
                    logging.debug(f"Moved {player.distance_from(position[0], position[1])} with expected max distance of {maximum_distance}, assuming bad OCR. {position} {last_position}")
                    last_ocr_position = position
                    continue
                elif player.distance_from(position[0], position[1]) == 0:
                    player.turn_to_random_bearing()
                    player.stuck()
                    continue
                else:
                    logging.debug(f"Position changed from {last_position} to {position}")
                    d_y = position[1] - last_position[1]
                    d_x = position[0] - last_position[0]
                    angle = math.degrees(math.atan2(d_y, d_x))
                    player.movement_direction = (90 - angle) % 360

            last_position = position
            player.x = position[0]
            player.y = position[1]
            player.z = position[2]

        #location = get_location(pillow_img)
        #compass = find_template(pillow_img, 'compass', threshold=0.75)
        #if len(compass) >= 1:
        else:
            logging.debug("Could not get position for this frame.")
            P.turn_to_random_bearing()
            time.sleep(1)
            continue

        interaction = new_world.find_template('interact', threshold=0.75)
        can_interact = True if len(interaction) > 0 else False
        #interactables += find_template(pillow_array, 'interactable', threshold=0.7)
        #interactables += find_template(pillow_array, 'large_interactable', threshold=0.7)
        #interactables = imutils.object_detection.non_max_suppression(numpy.array(interactables))

        if can_interact:
            interaction = new_world.get_interactable(interaction[0])

        #print(f"Position: {position}")
        #print(f"Location: {location}")
        #print(f"Heading: {heading}")
        if can_interact:
            logging.debug(f"Interaction: {interaction}")
            player.interact()
            continue
        #if len(interactables) > 0:
        #    print(f"Found {len(interactables)} interactables:")
        #    for interactable in interactables:
        #        print(interactable)
        #else:
        #    print("No interactables found.")

        if position[0] is not None:
            player_x = position[0]
            player_y = position[1]
            nearby_items = []
            logging.debug(f"Scanning database for nearby stuff")
            for resource in markers.keys():
                if resource in ("areas", "documents", "monsters", "npc", "pois"):
                    continue
                for region in markers[resource].keys():
                    if region in ('nut', 'herb', 'berry', 'cranberry', 'saltpeter'):
                        continue
                    for item in markers[resource][region].keys():
                        loc_x = markers[resource][region][item]['x']
                        loc_y = markers[resource][region][item]['y']

                        dist_x = player_x - loc_x
                        dist_y = player_y - loc_y
                        dist = distance(player_x, player_y, loc_x, loc_y)

                        if dist < DETECTION_DISTANCE:
                            dir_x = 'E' if dist_x < 0 else 'W'
                            dir_y = 'N' if dist_y < 0 else 'S'

                            name = f"{resource}.{region}.{item}"
                            bearing = round(math.degrees(math.atan2(dist_y, dist_x)) + 450) % 360
                            nearby_items.append((name, round(dist), abs(round(dist_x)), abs(round(dist_y)), dir_x, dir_y, bearing))

            nearby_items.sort(key=lambda x: x[1])
            # print('-----')
            # for i in nearby_items[:10]:
            #     print(f"{i[0]} ({i[1]}m bearing {i[6]}): {i[2]}{i[4]} {i[3]}{i[5]}")

        if player.bearing_offset_x > 0 or player.bearing_offset_y > 0:
            P.restore_bearing()
        # P.move_to_destination()

        logging.debug("/loop")

        if not loop:
            break

        time.sleep(1)
    # print(get_fps(spillow_img))

    # find_template(cv2.cvtColor(numpy.array(pillow_img), cv2.COLOR_RGB2GRAY), 'button')


if __name__ == '__main__':
    main()
