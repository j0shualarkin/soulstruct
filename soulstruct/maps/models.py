from io import BufferedReader, BytesIO
from enum import IntEnum

from soulstruct.maps.core import MSBEntry
from soulstruct.utilities import BinaryStruct, read_chars_from_buffer


class MODEL_TYPE(IntEnum):
    MapPiece = 0
    Object = 1
    Enemy = 2
    Player = 4
    Collision = 5
    Navmesh = 6


class MSBModel(MSBEntry):

    MODEL_STRUCT = BinaryStruct(
        ('name_offset', 'i'),
        ('model_type', 'i'),
        ('model_type_index', 'i'),
        ('sib_path_offset', 'i'),
        ('instance_count', 'i'),
        '12x',
    )

    def __init__(self, msb_model_source):
        super().__init__()
        self.model_type = -1
        self._model_type_index = None  # not sure if this matters.
        self.sib_path = ''
        self._instance_count = None

        if isinstance(msb_model_source, bytes):
            msb_model_source = BytesIO(msb_model_source)
        if isinstance(msb_model_source, BufferedReader):
            self.unpack(msb_model_source)
        else:
            raise TypeError(f"'msb_model_source' must be a buffer or bytes, not {type(msb_model_source)}")

    def unpack(self, msb_buffer):
        model_offset = msb_buffer.tell()
        model_data = self.MODEL_STRUCT.unpack(msb_buffer)
        self.name = read_chars_from_buffer(
            msb_buffer, offset=model_offset + model_data.name_offset, encoding='shift-jis')
        self.sib_path = read_chars_from_buffer(
            msb_buffer, offset=model_offset + model_data.sib_path_offset, encoding='shift-jis')
        self.model_type = MODEL_TYPE(model_data.model_type)
        self._model_type_index = model_data.model_type_index
        self._instance_count = model_data.instance_count

    def pack(self):
        name_offset = self.MODEL_STRUCT.size
        packed_name = self.get_name_to_pack().encode('shift-jis') + b'\0'
        sib_path_offset = name_offset + len(packed_name)
        packed_sib_path = self.sib_path.encode('shift-jis') + b'\0' if self.sib_path else b'\0' * 6
        while len(packed_name + packed_sib_path) % 4 != 0:
            packed_sib_path += b'\0'
        packed_model_data = self.MODEL_STRUCT.pack(
            name_offset=name_offset,
            model_type=MODEL_TYPE(self.model_type).value,
            model_type_index=self._model_type_index,
            sib_path_offset=sib_path_offset,
            instance_count=self._instance_count,
        )
        return packed_model_data + packed_name + packed_sib_path

    def set_indices(self, model_type_index, instance_count):
        self._model_type_index = model_type_index
        self._instance_count = instance_count
