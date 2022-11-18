# Room Data Generation

`room_conv.py` generates the resulting mapping in `room_to_surl.json`. Since automatically fetching all this data is a nightmare, fetching and combining this data is a manual process -- only run `room_conv.py` when room data changes significantly and once the sources have been updated.

To get the url for a room's timetable, a few separate room name maps need to be combined. Tabula names are almost exactly the campus map names. Tabula's source code provides a mapping from Tabula to Sciencia's (room booking system's) internal room names. The form when selecting a room timetable to view gives the mapping from Sciencia names to the required url parameter.

## Files used
- Warwick provides maps: tabula (~campus map) to scientia (timetable management), and scientia to room booking url key.
- These are in `tabula-sciencianame.txt"` and `scientianame-url.txt` respectively.
- Custom mapping for Campus Map to Tabula are in `custom-maptotab.txt`
- Custom room names on the Tabula to Sciencia step are in `custom-tabstoname.txt`
- `room_to_surl.json` is the final resulting mapping

- `central-room-data.json` holds data for the list of centrally timetabled rooms (rooms that are bookable through uni timetabling, and a ITS AV page exists for)
- Some people may want to search for a room under a different name, these are listed in `room-mapname.txt`. This has to be separate as a pre-processing step to the Campus Map API, whereas all others are after the request. 


## Updating the room mapping
These data sources are all a mess to get at and translate, so a few steps are manual.

1. Update central room info `central-room-data.json` periodically from https://warwick.ac.uk/services/its/servicessupport/av/lecturerooms/roominformation/room-data.js
2. Convert result from js to json, e.g. with https://www.convertsimple.com/convert-javascript-to-json/
3. Update tabula mapping `tabula-sciencianame.txt` from Tabula src code: common/src/main/scala/uk/ac/warwick/tabula/services/timetables/ScientiaCentrallyManagedRooms.scala
4. Chop off ends and comments, then can regex convert `"(.+)"` -> `MapLocation\("(.+)", "(\d+)", Some\("(.+)"\)\),` to `$2 | $1`
5. Update scientia mapping `scientianame-url.txt` from http://go.warwick.ac.uk/timetablereports > Locations > Open Dev Tools > Inspect "Select Room(s)" menu, and copy out internal HTML
6. Convert with regex convert `\t*<option value="([^"]+)">([^<]+)</option>` -> `$2 | $1`