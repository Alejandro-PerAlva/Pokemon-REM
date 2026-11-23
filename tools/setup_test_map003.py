import rubymarshal.reader as r
import rubymarshal.writer as w
import copy

path = 'Data/Map003.rxdata'
data = r.load(open(path, 'rb'))
events = [v for k, v in data.attributes.items() if 'event' in str(k).lower()][0]

# 1. Update EV002 (at 29, 7) to give ITEMFINDER as well
ev2 = events[2]
p0 = ev2.attributes['@pages'][0]
cmd_item = copy.deepcopy(p0.attributes['@list'][0])
cmd_item.attributes['@code'] = 355
cmd_item.attributes['@parameters'] = [b'Kernel.pbReceiveItem(PBItems::ITEMFINDER)']
# Check if already has it
has_it = any(b'ITEMFINDER' in b''.join(c.attributes.get('@parameters', [])) for c in p0.attributes['@list'])
if not has_it:
    p0.attributes['@list'].insert(2, cmd_item)

# 2. Create Event 14 (HiddenItem) at x=33, y=9
ev_hidden = copy.deepcopy(ev2)
ev_hidden.attributes['@id'] = 14
ev_hidden.attributes['@name'] = b'HiddenItem'
ev_hidden.attributes['@x'] = 33
ev_hidden.attributes['@y'] = 9

# Page 0
hp0 = ev_hidden.attributes['@pages'][0]
hp0.attributes['@graphic'].attributes['@character_name'] = b''
hp0.attributes['@graphic'].attributes['@tile_id'] = 0
hp0.attributes['@trigger'] = 0  # Action button

c1 = copy.deepcopy(cmd_item)
c1.attributes['@code'] = 355
c1.attributes['@parameters'] = [b'Kernel.pbItemBall(:SUPERPOTION)']

c2 = copy.deepcopy(cmd_item)
c2.attributes['@code'] = 355
c2.attributes['@parameters'] = [b'$game_self_switches[[$game_map.map_id, @event_id, "A"]] = true']

c_end = copy.deepcopy(p0.attributes['@list'][-1])
c_end.attributes['@code'] = 0
c_end.attributes['@parameters'] = []

hp0.attributes['@list'] = [c1, c2, c_end]

# Page 1 (Self switch A active -> empty)
hp1 = copy.deepcopy(hp0)
hp1.attributes['@condition'].attributes['@self_switch_valid'] = True
hp1.attributes['@condition'].attributes['@self_switch_ch'] = b'A'
hp1.attributes['@list'] = [copy.deepcopy(c_end)]

ev_hidden.attributes['@pages'] = [hp0, hp1]
events[14] = ev_hidden

with open(path, 'wb') as f:
    f.write(w.writes(data))

print('Map003 successfully configured with EV002 (gives ITEMFINDER) and Event 14 (HiddenItem at 33, 9)!')
