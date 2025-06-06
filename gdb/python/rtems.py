#!/usr/bin/env python3

import gdb

class RtemsCommand(gdb.Command):
    def __init__(self):
        super().__init__('rtems', gdb.COMMAND_STATUS, gdb.COMPLETE_NONE, True)

THREAD_STATES = {
    0x00000000: "STATES_READY",
    0x00000001: "STATES_WAITING_FOR_MUTEX",
    0x00000002: "STATES_WAITING_FOR_SEMAPHORE",
    0x00000004: "STATES_WAITING_FOR_EVENT",
    0x00000008: "STATES_WAITING_FOR_SYSTEM_EVENT",
    0x00000010: "STATES_WAITING_FOR_MESSAGE",
    0x00000020: "STATES_WAITING_FOR_CONDITION_VARIABLE",
    0x00000040: "STATES_WAITING_FOR_FUTEX",
    0x00000080: "STATES_WAITING_FOR_BSD_WAKEUP",
    0x00000100: "STATES_WAITING_FOR_TIME",
    0x00000200: "STATES_WAITING_FOR_PERIOD",
    0x00000400: "STATES_WAITING_FOR_SIGNAL",
    0x00000800: "STATES_WAITING_FOR_BARRIER",
    0x00001000: "STATES_WAITING_FOR_RWLOCK",
    0x00002000: "STATES_WAITING_FOR_JOIN_AT_EXIT",
    0x00004000: "STATES_WAITING_FOR_JOIN",
    0x00008000: "STATES_SUSPENDED",
    0x00010000: "STATES_WAITING_FOR_SEGMENT",
    0x00020000: "STATES_LIFE_IS_CHANGING",
    0x08000000: "STATES_DEBUGGER",
    0x10000000: "STATES_INTERRUPTIBLE_BY_SIGNAL",
    0x20000000: "STATES_WAITING_FOR_RPC_REPLY",
    0x40000000: "STATES_ZOMBIE",
    0x80000000: "STATES_DORMANT",
}

WAIT_CLASS = {
    0x100: "THREAD_WAIT_CLASS_EVENT",
    0x200: "THREAD_WAIT_CLASS_SYSTEM_EVENT",
    0x400: "THREAD_WAIT_CLASS_OBJECT",
    0x800: "THREAD_WAIT_CLASS_PERIOD",
}

OBJECT_CLASSES = {

}

def _thr_state_name(state: int) -> str:
    """
    Convert a thread state to its associated name
    
    Parameters
    ----------
    state : int
        State, comes from the thread control block
    """
    try:
        return THREAD_STATES[state]
    except:
        return f'Invalid ({state})'
        
def _wait_class_flags(cls: int) -> list[str]:
    """
    Converts the wait class of a thread into a list of named flags

    Parameters
    ----------
    cls : int
        Wait class, as part of the Wait struct.
    """
    l = []
    for k,v in WAIT_CLASS.items():
        if cls & k: l.append(v)
    return l

def _decode_name(name: int) -> str:
    """
    Decodes a name into a printable string
    """
    chrs = [(name>>24) & 0xFF,
            (name>>16) & 0xFF,
            (name>>8 ) & 0xFF,
            (name>>0 ) & 0xFF]
    return ''.join([chr(x) for x in chrs if x != 0])

def _object_class(id: int):
    """
    Extract object class from objects id
    """
    return (id >> 27) & 0x1F

class RtemsTasksCommand(gdb.Command):
    """
    Command to list tasks
    """
    def __init__(self):
        super().__init__('rtems tasks', gdb.COMMAND_USER)
    
    def _iterate_tasks(self):
        """
        Iterate tasks and print info about them
        """
        i = 0
        while True:
            # Grab the object
            obj = gdb.parse_and_eval(f'_RTEMS_tasks_Information.Objects.local_table[{i}]')
            # Cast to thread control structure
            ctrl = obj.cast(gdb.lookup_type('Thread_Control').pointer())

            # Instruction pointer is on the top of the stack
            reg = ctrl['Registers']['esp']
            pc = reg.cast(gdb.lookup_type('uint32_t').pointer()).dereference() if int(reg) != 0 else 0

            name = _decode_name(obj['name']['name_u32'])
            print(f'{name} -->')
            print(f'  State: {_thr_state_name(int(ctrl["current_state"]))}')
            print(f'  Wait State:')
            print(f'    Class: {", ".join(_wait_class_flags(ctrl["Wait"]["flags"]))}')
            print(f'  PC: {hex(pc)}')
            if int(obj['Node']['next']) == 0 or i > 128:
                break
            i += 1
    
    def invoke(self, argument, from_tty):
        self._iterate_tasks()


class RtemsSemaphoresCommand(gdb.Command):
    def __init__(self):
        super().__init__('rtems sem', gdb.COMMAND_USER)
    
    def _iterate_sems(self, locked_only: bool):
        # Head node
        node = gdb.parse_and_eval('_Semaphore_Objects[0]')
        while True:
            # Grab the core control union
            ctrl = node['Core_control']
            # Grab the wait queue. This is at the same offset for all types in the union
            wait_q = ctrl['Semaphore']['Wait_queue']['Queue']

            is_locked = wait_q['owner'] != 0

            if locked_only and is_locked or not locked_only:
                name = _decode_name(int(node["Object"]["name"]["name_u32"]))
                print(f'{name if len(name) else '<unnamed>'} -->')
                print(f'  Status: {"Locked" if is_locked else "Unlocked"}')
                if is_locked:
                    print(f'    Owner: {wait_q["owner"].cast(gdb.lookup_type('Thread_Control').pointer())}')

            # Next node
            next = node['Object']['Node']['next']
            if int(next) == 0: break
            node = next.cast(gdb.lookup_type('Semaphore_Control').pointer())

    def invoke(self, arg, from_tty):
        self._iterate_sems(arg=='locked')

RtemsCommand()
RtemsTasksCommand()
RtemsSemaphoresCommand()