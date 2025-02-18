import pygame
import pickle
from pathlib import Path
from pydantic import BaseModel
import json


def build_default_keys():
    """
    Build Keys object with default key bindings and reserved keys.
    """
    keys = Keys(reserved_keys=RESERVED_KEYS)
    for command_name in DEFAULT_BINDINGS:
        for values in DEFAULT_BINDINGS[command_name]:
            keys.register(
                command_name=command_name,
                key=values[0],
                can_shift=values[1],
                editable=values[2])
    return keys


class Keys():

    def __init__(self, reserved_keys=[]):
        self.__reserved_keys = reserved_keys
        self.__commands = {}
        self.__key_to_command_names = {}

    def __eq__(self, x):
        """Check if equal to this class instance."""
        if not isinstance(x, Keys):
            return False
        if len(x.commands) != len(self.commands):
            return False
        if len(x.reserved_keys) != len(self.reserved_keys):
            return False
        for key in x.reserved_keys:
            if key not in self.reserved_keys:
                return False
        for cmd in x.commands:
            if cmd not in self.commands:
                return False
            if x.commands[cmd] != self.commands[cmd]:
                return False
        return True

    def __getitem__(self, key):
        return self.__commands[key]

    def get_command_names(self, key):
        """
        Return list of command names associated to key.

        Parameters
        ----------
        key : int
            Key index for Pygame.

        Returns
        -------
        List:
            List of command names.
        """
        return self.__key_to_command_names.get(key, [])

    @property
    def command_names(self):
        return list(self.__commands.keys())

    @property
    def commands(self):
        return self.__commands

    @property
    def reserved_keys(self):
        return self.__reserved_keys

    def is_reserved(self, key):
        if isinstance(key, Binding):
            return key.key in self.reserved_keys
        return key in self.reserved_keys

    def register(
            self,
            command_name,
            key,
            can_shift,
            editable
    ):
        """
        Register a key binding for a command.

        Parameters
        ----------
        command_name : str
            Name of command.
        key : int
            Key index for Pygame.
        can_shift : bool
            If can be used with shift.
        editable : bool
            If editable.
        """
        binding = Binding(key=key, can_shift=can_shift, editable=editable)
        if self.is_reserved(key):
            if binding.editable:
                msg = f'Binding of reserved key cannot be editable "{binding}"'
                raise ValueError(msg)
        if command_name not in self.commands:
            self.commands[command_name] = []
        self.commands[command_name].append(binding)
        if key not in self.__key_to_command_names:
            self.__key_to_command_names[key] = []
        self.__key_to_command_names[key].append(command_name)


class Binding(BaseModel):
    key: None | int
    can_shift: bool
    editable: bool


def save_keys(keys, filepath):
    """
    Save keys to filepath. 
    File type must be either .json or .pickle.
    """
    p = Path(filepath)
    if p.suffix.lower() == '.pickle':
        with open(p, 'wb') as file:
            pickle.dump(keys, file)
    elif p.suffix.lower() == '.json':
        data = {'reserved_keys': keys.reserved_keys, 'commands': {}}
        for cmd in keys.commands:
            cmd_bindings = []
            for b in keys.commands[cmd]:
                cmd_bindings.append(b.model_dump())
            data['commands'][cmd] = cmd_bindings
        with open(p, 'w', encoding='utf-8') as file:
            file.write(json.dumps(data, indent=4))
    else:
        raise NotImplementedError('Filetype must be .json or .pickle')


def load_keys(filepath):
    """
    Load keys from filepath.
    File type must be either .json or .pickle.
    """
    p = Path(filepath)
    if p.suffix.lower() == '.pickle':
        with open(p, 'rb') as file:
            return pickle.load(file)
    elif p.suffix.lower() == '.json':
        try:
            with open(p, 'r', encoding='utf-8') as file:
                data = json.load(file)
            keys = Keys(reserved_keys=data['reserved_keys'])
            for command_name in data['commands']:
                for x in data['commands'][command_name]:
                    keys.register(
                        command_name=command_name,
                        key=x['key'],
                        can_shift=x['can_shift'],
                        editable=x['editable'])
            return keys
        except Exception as e:
            raise e
    else:
        raise NotImplementedError('Filetype must be .json or .pickle')


# Key, shift, editable
DEFAULT_BINDINGS = {
    'move north': ((pygame.locals.K_UP, False, False), (pygame.locals.K_KP8, False, True)),
    'move south': ((pygame.locals.K_DOWN, False, False), (pygame.locals.K_KP2, False, True)),
    'move west': ((pygame.locals.K_LEFT, False, False), (pygame.locals.K_KP4, False, True)),
    'move east': ((pygame.locals.K_RIGHT, False, False), (pygame.locals.K_KP6, False, True)),
    'move northwest': ((None, False, True), (pygame.locals.K_KP7, False, True)),
    'move northeast': ((None, False, True), (pygame.locals.K_KP9, False, True)),
    'move southwest': ((None, False, True), (pygame.locals.K_KP1, False, True)),
    'move southeast': ((None, False, True), (pygame.locals.K_KP3, False, True)),
    'wait': ((pygame.locals.K_PERIOD, False, True), (pygame.locals.K_KP5, False, True)),
    'repeat last attack': ((pygame.locals.K_r, False, True), (None, False, True)),
    'repeat second last attack': ((pygame.locals.K_r, True, True), (None, False, True)),
    'look': ((pygame.locals.K_l, False, True), (None, False, True)),
    'go down': ((pygame.locals.K_GREATER, False, True), (pygame.locals.K_LESS, True, True)),
    'go up': ((pygame.locals.K_LESS, False, True), (None, False, True)),
    'mine': ((pygame.locals.K_m, False, True), (None, False, True)),
    'pick up': ((pygame.locals.K_COMMA, False, True), (None, False, True)),
    'drop': ((pygame.locals.K_d, False, True), (None, False, True)),
    'throw': ((pygame.locals.K_t, False, True), (None, False, True)),
    'inventory': ((pygame.locals.K_i, False, True), (None, False, True)),
    'information': ((pygame.locals.K_i, True, True), (None, False, True)),
    'consume': ((pygame.locals.K_c, False, True), (None, False, True)),
    'cook': ((pygame.locals.K_c, True, True), (None, False, True)),
    'wield': ((pygame.locals.K_w, False, True), (None, False, True)),
    'wear': ((pygame.locals.K_w, True, True), (None, False, True)),
    'unwield': ((pygame.locals.K_u, False, True), (None, False, True)),
    'undress': ((pygame.locals.K_u, True, True), (None, False, True)),
    'choose stance': ((pygame.locals.K_s, False, True), (None, False, True)),
    'pray': ((pygame.locals.K_p, False, True), (None, False, True)),
    'frighten': ((pygame.locals.K_f, False, True), (None, False, True)),
    'cast a spell': ((pygame.locals.K_m, True, True), (None, False, True)),
    'read': ((pygame.locals.K_l, True, True), (None, False, True)),
    'write': ((pygame.locals.K_s, True, True), (None, False, True)),
    'list bodyparts': ((pygame.locals.K_b, False, True), (None, False, True)),
    'choose bodyparts': ((pygame.locals.K_b, True, True), (None, False, True)),
    'help': ((pygame.locals.K_h, False, True), (None, False, True)),
    'log up': ((pygame.locals.K_PAGEUP, False, True), (None, False, True)),
    'log down': ((pygame.locals.K_PAGEDOWN, False, True), (None, False, True)),
    'log start': ((pygame.locals.K_HOME, False, True), (None, False, True)),
    'log end': ((pygame.locals.K_END, False, True), (None, False, True)),
    'list up': ((pygame.locals.K_UP, False, False), (None, False, True)),
    'list down': ((pygame.locals.K_DOWN, False, False), (None, False, True)),
    'list select': ((pygame.locals.K_RETURN, False, False), (None, False, True)),
    'escape': ((pygame.locals.K_ESCAPE, False, False), (None, False, True)),
}

RESERVED_KEYS = [
    pygame.locals.K_UP,
    pygame.locals.K_DOWN,
    pygame.locals.K_LEFT,
    pygame.locals.K_RIGHT,
    pygame.locals.K_RETURN,
    pygame.locals.K_ESCAPE,
    pygame.locals.K_LSHIFT,
]
