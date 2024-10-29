from csv import DictReader

def get_room_row(number, rooms):
    for room in rooms:
        if room['room_number'] == number:
            return room

    return None

def report_validator(response, **kwargs):
    """Confirm results are actually in csv"""

    content = response.content.decode('ascii').split('\n')
    a_dict = DictReader(content)

    items = []
    for elem in a_dict:
        items.append(elem)

    if 'rows' in kwargs:
        for row in kwargs['rows']:
            assert 'room_number' in row
            room = get_room_row(row['room_number'], items)
            assert room
            for field, value in row.items():
                if field == 'room_number':
                    continue

                assert field in room
                print(f"Checking {row['room_number']} for {field}:{value} (actual {room[field]})")
                assert room[field] == value
