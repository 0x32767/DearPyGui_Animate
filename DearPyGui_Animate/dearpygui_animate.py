"""
---------------------------------------------
dearpygui animations add-on

https://github.com/mrtnRitter/DearPyGui_Animate

v0.12
----------------------------------------------
"""

# -----------------------------------------------------------------------------
# 				Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass

import dearpygui.dearpygui as dpg

# -----------------------------------------------------------------------------
# 				Global Registers
# -----------------------------------------------------------------------------

animations: list[Animation] = []
delta_positions = []
delta_sizes = []
delta_opacities = []

# -----------------------------------------------------------------------------
# 				Animation dataclasses
# -----------------------------------------------------------------------------

@dataclass()
class Animation:
    animation_name: any
    animation_type: str # either: position size opacity
    object_name: any
    start_value: any
    distance: any
    ease: any
    duration: int
    starttime: any
    frame_counter: int
    last_ease: int
    loop: str # either: ping-pong cycle continue
    loop_counter: int
    callback_function: any
    function_data: any
    early_callback: any
    early_callback_data: any
    isplaying: bool
    ispaused: bool
    isreversed: bool

# -----------------------------------------------------------------------------
# 				Main Functions
# -----------------------------------------------------------------------------

def add(type, object, startval, endval, ease, duration, **kwargs):
    """
    adds a new animation to animations register
    """

    # fix min-values: smallest size window = 32x32, smallest size item = 1x1
    if type == "size":
        if dpg.get_item_type(object) == "mvAppItemType::Window":
            for i in range(2):
                if startval[i] < 32:
                    startval[i] = 32

                elif endval[i] < 32:
                    endval[i] = 32
        else:
            for i in range(2):
                if startval[i] < 1:
                    startval[i] = 1

                elif endval[i] < 1:
                    endval[i] = 1

    # rewrite endval to distance, all calculations are based on distance
    try:
        distance = [endval[0] - startval[0], endval[1] - startval[1]]
    except Exception:
        distance = endval - startval

    options = {
        "name": "",
        "timeoffset": 0,
        "loop": "",
        "callback": "",
        "callback_data": "",
        "early_callback": "",
        "early_callback_data": ""
    }
    options.update(kwargs)

    starttime = dpg.get_total_time() + options["timeoffset"]
    framecounter = 0
    last_ease = 0
    loopcounter = 0
    isplaying = False
    ispaused = False
    isreversed = False

    new_animation = Animation(
        options["name"],
        type,
        object,
        startval,
        distance,
        ease,
        duration,
        starttime,
        framecounter,
        last_ease,
        options["loop"],
        loopcounter,
        options["callback"],
        options["callback_data"],
        options["early_callback"],
        options["early_callback_data"],
        isplaying,
        ispaused,
        isreversed
    )

    global animations
    animations.append(new_animation)


def run():
    """
    Animation data-set layout:

    animation[0] = animation name
    animation[1] = animation type
    animation[2] = object name
    animation[3] = start value
    animation[4] = distance
    animation[5] = ease
    animation[6] = duration
    animation[7] = starttime
    animation[8] = frame counter
    animation[9] = last ease
    animation[10] = loop
    animation[11] = loop counter
    animation[12] = callback function
    animation[13] = function data
    animation[14] = early callback
    animation[15] = early callback data
    animation[16] = isplaying
    animation[17] = ispaused
    animation[18] = isreversed
    """

    animations_updated: list[Animation] = []
    callbacks = {}
    global animations

    for animation in animations:

        if dpg.get_total_time() >= animation.starttime and not animation.ispaused:

            if animation.early_callback and animation.frame_counter == 0:
                callbacks[animation.early_callback] = (animation.object_name, animation.early_callback_data)

            animation.isplaying = True
            frame = animation.frame_counter / animation.duration
            ease = BezierTransistion(frame, animation.ease)

            if animation.animation_type == "position":
                add_delta_positions(animation, ease)

            elif animation.animation_type == "size":
                add_delta_sizes(animation, ease)

            elif animation.animation_type == "opacity":
                add_delta_opacities(animation, ease)

            animation.last_ease = ease

            if animation.frame_counter < animation.duration:
                if not animation.isreversed:
                    animation.frame_counter += 1
                else:
                    if animation.frame_counter == 0:
                        animation.isreversed = False
                        animation.frame_counter = 1
                    else:
                        animation.frame_counter -= 1
                animations_updated.append(animation)

            elif animation.frame_counter == animation.duration:
                if animation.loop:
                    set_loop(animation, animations_updated)

                if animation.callback_function:
                    callbacks[animation.callback_function] = (animation.object_name, animation.function_data)

        else:
            animations_updated.append(animation)

    set_pos()
    set_size()
    set_opacity()

    animations = animations_updated

    for func, dat in callbacks.items(): # TODO tuple unpack `dat`
        func(dat[0], dat[1])


def play(animation_name):
    """
    resumes an animation
    """

    global animations

    for animation in animations:
        if animation.animation_name == animation_name:
            animation.ispaused = False


def pause(animation_name):
    """
    pauses an animation
    """

    global animations

    for animation in animations:
        if animation.animation_name == animation_name:
            animation.ispaused = True


def remove(animation_name):
    """
    removes an animation from animations register
    """

    animations_updated = []
    delta_positions_updated = []
    delta_sizes_updated = []
    delta_opacities_updated = []
    object_anitype = []
    global animations
    global delta_positions
    global delta_sizes
    global delta_opacities

    for animation in animations:
        if not animation.animation_name == animation_name:
            animations_updated.append(animation)
        else:
            object_anitype = [animation.object_name, animation.animation_type]

    if object_anitype:
        found = False
        for ani in animations_updated:
            if ani.object_name == object_anitype[0] and ani.animation_type == object_anitype[1]:
                found = True
                break

        if not found:
            if object_anitype[1] == "position":
                for entry in delta_positions:
                    if not entry[0] == object_anitype[0]:
                        delta_positions_updated.append(entry)
                delta_positions = delta_positions_updated

            elif object_anitype[1] == "size":
                for entry in delta_sizes:
                    if not entry[0] == object_anitype[0]:
                        delta_sizes_updated.append(entry)
                delta_sizes = delta_sizes_updated

            elif object_anitype[1] == "opacity":
                for entry in delta_opacities:
                    if not entry[0] == object_anitype[0]:
                        delta_opacities_updated.append(entry)
                delta_opacities = delta_opacities_updated

    animations = animations_updated


def get(*args):
    """
    return animation data as requested
    """

    return_data = []
    global animations

    for animation in animations:
        for entry in args:
            if entry == "name":
                return_data.append(animation.animation_name)

            if entry == "type":
                return_data.append(animation.animation_type)

            if entry == "object":
                return_data.append(animation.object_name)

            if entry == "startval":
                return_data.append(animation.start_value)

            if entry == "endval":
                try:
                    endval = [animation.start_value[0] + animation.distance[0], animation.start_value[1] + animation.distance[1]]
                except Exception:
                    endval = animation.start_value + animation.distance
                return_data.append(endval)

            if entry == "ease":
                return_data.append(animation.ease)

            if entry == "duration":
                return_data.append(animation.duration)

            if entry == "starttime":
                return_data.append(animation.starttime)

            if entry == "framecounter":
                return_data.append(animation.frame_counter)

            if entry == "loop":
                return_data.append(animation.loop)

            if entry == "loopcounter":
                return_data.append(animation.loop_counter)

            if entry == "callback":
                return_data.append(animation.callback_function)

            if entry == "callback_data":
                return_data.append(animation.function_data)

            if entry == "early_callback":
                return_data.append(animation.early_callback)

            if entry == "early_callback_data":
                return_data.append(animation.early_callback_data)

            if entry == "isplaying":
                return_data.append(animation.ispaused)

            if entry == "ispaused":
                return_data.append(animation.ispaused)

    if not return_data:
        return False

    else:
        return return_data


# -----------------------------------------------------------------------------
# 				Helper Functions
# -----------------------------------------------------------------------------

def BezierTransistion(search, handles):
    """
    solving y (progress) of bezier curve for given x (time)
    using the newton-raphson method
    """

    h1x, h1y, h2x, h2y = handles

    cx = 3 * h1x
    bx = 3 * (h2x - h1x) - cx
    ax = 1 - cx - bx

    t = search

    for i in range(100):
        x = (ax * t ** 3 + bx * t ** 2 + cx * t) - search

        if round(x, 4) == 0:
            break

        dx = 3.0 * ax * t ** 2 + 2.0 * bx * t + cx

        t -= (x / dx)

    return 3 * t * (1 - t) ** 2 * h1y + 3 * t ** 2 * (1 - t) * h2y + t ** 3


def set_loop(animation: Animation, animations_updated):
    """
    prepare animation for next loop iteration
    """

    if animation.loop == "ping-pong":
        animation.isreversed = True
        animation.frame_counter -= 1
        animation.last_ease = 1

    elif animation.loop == "cycle":
        animation.frame_counter = 0
        animation.last_ease = 0

    elif animation.loop == "continue":
        try:
            animation.start_value = [animation.start_value[0] + animation.distance[0], animation.start_value[1] + animation.distance[1]]
        except Exception:
            animation.start_value += animation.distance
        animation.frame_counter = 0
        animation.last_ease = 0

    animation.loop_counter += 1
    animations_updated.append(animation)


def add_delta_positions(animation: Animation, ease):
    """
    collects delta movements of all position animations for a certain item
    """

    global delta_positions

    for item in delta_positions:
        if animation.object_name == item[0]:

            x_step = animation.distance[0] * (ease - animation.last_ease)
            y_step = animation.distance[1] * (ease - animation.last_ease)

            item[1] += x_step
            item[2] += y_step

            if animation.frame_counter < animation.duration or animation.loop:
                item[3] = True

            if animation.loop == "cycle" and animation.frame_counter == animation.duration:
                item[3] = False

            if animation.frame_counter == animation.duration and not item[3]:
                item[3] = False

            break
    else:
        delta_positions.append([animation.object_name, animation.start_value[0], animation.start_value[1], True])


def add_delta_sizes(animation: Animation, ease):
    """
    collects delta movements of all size animations for a certain item
    """

    global delta_sizes

    for item in delta_sizes:
        if animation.object_name == item[0]:
            w_step = animation.distance[0] * (ease - animation.last_ease)
            h_step = animation.distance[1] * (ease - animation.last_ease)

            item[1] += w_step
            item[2] += h_step

            if animation.frame_counter < animation.duration or animation.loop:
                item[3] = True

            if animation.loop == "cycle" and animation.frame_counter == animation.duration:
                item[3] = False

            if animation.frame_counter == animation.duration and not item[3]:
                item[3] = False

            break
    else:
        delta_sizes.append([animation.object_name, animation.start_value[0], animation.start_value[1], True])


def add_delta_opacities(animation: Animation, ease):
    """
    collects delta movements of all opacity animations for a certain item
    """

    global delta_opacities

    for item in delta_opacities:
        if animation.object_name == item[0]:
            o_step = animation.distance * (ease - animation.last_ease)

            item[1] += o_step

            if animation.frame_counter < animation.duration or animation.loop:
                item[2] = True

            if animation.loop == "cycle" and animation.frame_counter == animation.duration:
                item[2] = False

            if animation.frame_counter == animation.duration and not item[2]:
                item[2] = False

            break
    else:
        delta_opacities.append([animation.object_name, animation.start_value, True])


def set_pos():
    """
    moves the item
    """

    global delta_positions

    items_updated = []

    for item in delta_positions:
        if item[3] is None:
            items_updated.append(item)
            continue

        elif item[3]:
            x_int = int(item[1])
            y_int = int(item[2])

            item[3] = None

            items_updated.append(item)

        else:
            x_int = round(item[1])
            y_int = round(item[2])

        dpg.set_item_pos(item[0], [x_int, y_int])

    delta_positions = items_updated


def set_size():
    """
    set items size
    """

    global delta_sizes

    items_updated = []

    for item in delta_sizes:
        if item[3] is None:
            items_updated.append(item)
            continue

        elif item[3]:
            w_int = int(item[1])
            h_int = int(item[2])

            item[3] = None

            items_updated.append(item)

        else:
            w_int = round(item[1])
            h_int = round(item[2])

        dpg.set_item_width(item[0], w_int)
        dpg.set_item_height(item[0], h_int)

    delta_sizes = items_updated


def dpg_get_alpha_style(item):
    theme = dpg.get_item_theme(item)
    if theme is None:
        theme = dpg.add_theme()
        theme_component = dpg.add_theme_component(dpg.mvAll, parent=theme)
        alpha_style = dpg.add_theme_style(dpg.mvStyleVar_Alpha, 1, category=dpg.mvThemeCat_Core, parent=theme_component)
        dpg.bind_item_theme(item, theme)
        return alpha_style

    all_components = dpg.get_item_children(theme, 1)
    theme_component = None
    for component in all_components:
        if dpg.get_item_configuration(component)['item_type'] == dpg.mvAll:
            theme_component = component
            break
    if theme_component is None:
        theme_component = dpg.add_theme_component(parent=theme)

    all_styles = dpg.get_item_children(theme_component, 1)
    alpha_style = None
    for style in all_styles:
        if dpg.get_item_configuration(style)['target'] == dpg.mvStyleVar_Alpha:
            alpha_style = style
            break
    if alpha_style is None:
        alpha_style = dpg.add_theme_style(dpg.mvStyleVar_Alpha, 1, category=dpg.mvThemeCat_Core, parent=theme_component)
    return alpha_style


def set_opacity():
    """
    set items opacity
    """

    global delta_opacities

    items_updated = []

    for item in delta_opacities:
        if item[2] is None:
            items_updated.append(item)
            continue

        elif item[2]:
            item[2] = None
            items_updated.append(item)

        if dpg.get_item_type(item[0]) == "mvAppItemType::mvText":
            new_color = dpg.get_item_configuration(item[0])["color"]
            new_color = list(map(lambda color: int(color * 255), new_color[:3:]))

            new_color.append(item[1] * 255)

            dpg.configure_item(item[0], color=new_color)
        else:
            dpg.set_value(dpg_get_alpha_style(item[0]), [item[1]])

    delta_opacities = items_updated
