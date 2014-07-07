BLOCK_SIGNATURE = b'SBFF02'
DB_SIGNATURE = b'BTreeDB4'
WORLD_SIGNATURE = b'World2'

def pad_null(value, length):
    assert len(value) <= length, 'Value is too long'
    return value + b'\x00' * (length - len(value))

def write_world(path, base_world, root_node, root_is_leaf, alternate_root_node,
                alternate_root_is_leaf, blocks):
    """Writes a world file from scratch using the provided metadata and blocks.

    """
    # The last block will be a free block.
    blocks.append(b'FF\xFF\xFF\xFF\xFF' + b'\x00' * (base_world.block_size - 6))

    sbbf02_header = (
        '>ii?i',
        base_world.header_size,
        base_world.block_size,
        True,
        len(blocks) - 1),
    )

    btreedb4_header = (
        '>i?xi?xxxi?',
        base_world.key_size,
        False,
        root_node,
        root_is_leaf,
        alternate_root_node,
        alternate_root_is_leaf,
    )

    with open(path, 'wb') as f:
        f.write(BLOCK_SIGNATURE)
        f.write(struct.pack(*sbbf02_header)
        f.write(b'\x00' * (32 - f.tell()))
        f.write(pad_null(DB_SIGNATURE, 12))
        f.write(pad_null(base_world.identifier.encode('utf-8'), 12))
        f.write(struct.pack(*btreedb4_header)
        f.write(b'\x00' * (base_world.header_size - f.tell()))

        for block in blocks:
            f.write(block)
