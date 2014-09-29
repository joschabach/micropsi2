__author__ = 'jonas'


def get_voxel_blocktype(self, x, y, z):

    key = (x // 16, z // 16)
    columns = self.world.spockplugin.world.map.columns
    if key not in columns:
        return -1
    current_column = columns[key]
    if len(current_column.chunks) <= y // 16:
        return -1
    try:
        current_section = current_column.chunks[y // 16]
    except IndexError:
        return -1
    if current_section is None:
        return -1
    else:
        return current_section.get(x % 16, y % 16, z % 16).id
