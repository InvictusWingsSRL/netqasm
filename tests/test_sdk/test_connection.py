import logging

from qlink_interface import EPRType

from netqasm.sdk.connection import DebugConnection
from netqasm.sdk.qubit import Qubit
from netqasm.sdk.epr_socket import EPRSocket
from netqasm.logging import set_log_level
from netqasm.subroutine import Subroutine
from netqasm.encoding import RegisterName
from netqasm.parsing import deserialize
from netqasm.network_stack import CREATE_FIELDS, OK_FIELDS

from netqasm import instructions
from netqasm.instructions.operand import (
    Register,
    Immediate,
    Address,
    ArrayEntry,
    ArraySlice,
)

DebugConnection.node_ids = {
    "Alice": 0,
    "Bob": 1,
}


def test_simple():
    set_log_level(logging.DEBUG)
    with DebugConnection("Alice") as alice:
        q1 = Qubit(alice)
        q2 = Qubit(alice)
        q1.H()
        q2.X()
        q1.X()
        q2.H()

    # 4 messages: init, subroutine, stop app and stop backend
    assert len(alice.storage) == 4
    subroutine = deserialize(alice.storage[1].msg)
    expected = Subroutine(netqasm_version=(0, 0), app_id=0, commands=[
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.core.QAllocInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.InitInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(1),
        ),
        instructions.core.QAllocInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.InitInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.vanilla.GateHInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(1),
        ),
        instructions.vanilla.GateXInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.vanilla.GateXInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(1),
        ),
        instructions.vanilla.GateHInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        # NOTE qubits are now freed when application ends
        # without explicit qfree for each
        # Command(instruction=Instruction.SET, operands=[
        #     Register(RegisterName.Q, 0),
        #     0,
        # ]),
        # Command(instruction=Instruction.QFREE, operands=[
        #     Register(RegisterName.Q, 0),
        # ]),
        # Command(instruction=Instruction.SET, operands=[
        #     Register(RegisterName.Q, 0),
        #     1,
        # ]),
        # Command(instruction=Instruction.QFREE, operands=[
        #     Register(RegisterName.Q, 0),
        # ]),
    ])
    for command, expected_command in zip(subroutine.commands, expected.commands):
        print(repr(command))
        print(repr(expected_command))
        assert command == expected_command
    print(subroutine)
    print(expected)
    assert subroutine == expected


def test_rotations():
    set_log_level(logging.DEBUG)
    with DebugConnection("Alice") as alice:
        q = Qubit(alice)
        q.rot_X(n=1, d=1)

    # 4 messages: init, subroutine, stop app and stop backend
    assert len(alice.storage) == 4
    subroutine = deserialize(alice.storage[1].msg)
    expected = Subroutine(netqasm_version=(0, 0), app_id=0, commands=[
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.core.QAllocInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.InitInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.vanilla.RotXInstruction(
            qreg=Register(RegisterName.Q, 0),
            angle_num=Immediate(1),
            angle_denom=Immediate(1),
        ),
    ])
    for command, expected_command in zip(subroutine.commands, expected.commands):
        print(repr(command))
        print(repr(expected_command))
        assert command == expected_command
    print(subroutine)
    print(expected)
    assert subroutine == expected


def test_epr():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_node_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        q1 = epr_socket.create()[0]
        q1.H()

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    subroutine = deserialize(alice.storage[2].msg)
    print(subroutine)
    expected = Subroutine(netqasm_version=(0, 0), app_id=0, commands=[
        # Arg array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(OK_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(0),
        ),
        # Qubit address array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(1),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(1, index=Register(RegisterName.R, 1)),
        ),
        # ent info array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(CREATE_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(2),
        ),
        # tp arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(2, index=Register(RegisterName.R, 1)),
        ),
        # num pairs arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(2, index=Register(RegisterName.R, 1)),
        ),
        # create cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 3),
            value=Immediate(2),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 4),
            value=Immediate(0),
        ),
        instructions.core.CreateEPRInstruction(
            remote_node_id=Register(RegisterName.R, 0),
            epr_socket_id=Register(RegisterName.R, 1),
            qubit_addr_array=Register(RegisterName.R, 2),
            arg_array=Register(RegisterName.R, 3),
            ent_info_array=Register(RegisterName.R, 4),
        ),
        # wait cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(OK_FIELDS),
        ),
        instructions.core.WaitAllInstruction(
            slice=ArraySlice(
                address=Address(0),
                start=Register(RegisterName.R, 0),
                stop=Register(RegisterName.R, 1),
            ),
        ),
        # Hadamard
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.vanilla.GateHInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        # free qubit
        # NOTE qubits are now freed when application ends
        # without explicit qfree for each
        # Command(instruction=Instruction.SET, operands=[
        #     Register(RegisterName.Q, 0),
        #     0,
        # ]),
        # Command(instruction=Instruction.QFREE, operands=[
        #     Register(RegisterName.Q, 0),
        # ]),
        # return cmds
        instructions.core.RetArrInstruction(
            address=Address(0),
        ),
        instructions.core.RetArrInstruction(
            address=Address(1),
        ),
        instructions.core.RetArrInstruction(
            address=Address(2),
        ),
    ])
    for i, command in enumerate(subroutine.commands):
        print(repr(command))
        expected_command = expected.commands[i]
        print(repr(expected_command))
        print()
        assert command == expected_command
    print(subroutine)
    print(expected)
    assert subroutine == expected


def test_two_epr():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_node_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        qubits = epr_socket.create(number=2)
        qubits[0].H()
        qubits[1].H()

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    subroutine = deserialize(alice.storage[2].msg)
    print(subroutine)
    expected = Subroutine(netqasm_version=(0, 0), app_id=0, commands=[
        # Arg array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(2 * OK_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(0),
        ),
        # Qubit address array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(2),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(1, index=Register(RegisterName.R, 1)),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(1, index=Register(RegisterName.R, 1)),
        ),
        # ent info array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(CREATE_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 0),
            address=Address(2),
        ),
        # tp arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(2, index=Register(RegisterName.R, 1)),
        ),
        # num pairs arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(2),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(2, index=Register(RegisterName.R, 1)),
        ),
        # create cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 3),
            value=Immediate(2),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 4),
            value=Immediate(0),
        ),
        instructions.core.CreateEPRInstruction(
            remote_node_id=Register(RegisterName.R, 0),
            epr_socket_id=Register(RegisterName.R, 1),
            qubit_addr_array=Register(RegisterName.R, 2),
            arg_array=Register(RegisterName.R, 3),
            ent_info_array=Register(RegisterName.R, 4),
        ),
        # wait cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 0),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(2 * OK_FIELDS),
        ),
        instructions.core.WaitAllInstruction(
            slice=ArraySlice(
                address=Address(0),
                start=Register(RegisterName.R, 0),
                stop=Register(RegisterName.R, 1),
            ),
        ),
        # Hadamards
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(0),
        ),
        instructions.vanilla.GateHInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.Q, 0),
            value=Immediate(1),
        ),
        instructions.vanilla.GateHInstruction(
            qreg=Register(RegisterName.Q, 0),
        ),
        # return cmds
        instructions.core.RetArrInstruction(
            address=Address(0),
        ),
        instructions.core.RetArrInstruction(
            address=Address(1),
        ),
        instructions.core.RetArrInstruction(
            address=Address(2),
        ),
    ])
    for i, command in enumerate(subroutine.commands):
        print(repr(command))
        expected_command = expected.commands[i]
        print(repr(expected_command))
        print()
        assert command == expected_command
    print(subroutine)
    print(expected)
    assert subroutine == expected


def test_epr_m():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_node_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        outcomes = epr_socket.create(tp=EPRType.M)
        m = outcomes[0][2]
        with m.if_eq(0):
            m.add(1)

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    subroutine = deserialize(alice.storage[2].msg)
    print(subroutine)
    expected = Subroutine(netqasm_version=(0, 0), app_id=0, commands=[
        # Arg array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(OK_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 1),
            address=Address(0),
        ),
        # ent info array
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(CREATE_FIELDS),
        ),
        instructions.core.ArrayInstruction(
            size=Register(RegisterName.R, 1),
            address=Address(1),
        ),
        # tp arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(0),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 1),
            entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
        ),
        # num pairs arg
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(1),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 1),
            entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
        ),
        # create cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 3),
            value=Immediate(1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 4),
            value=Immediate(0),
        ),
        instructions.core.CreateEPRInstruction(
            remote_node_id=Register(RegisterName.R, 1),
            epr_socket_id=Register(RegisterName.R, 2),
            qubit_addr_array=Register(RegisterName.C, 0),
            arg_array=Register(RegisterName.R, 3),
            ent_info_array=Register(RegisterName.R, 4),
        ),
        # wait cmd
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 2),
            value=Immediate(OK_FIELDS),
        ),
        instructions.core.WaitAllInstruction(
            slice=ArraySlice(
                address=Address(0),
                start=Register(RegisterName.R, 1),
                stop=Register(RegisterName.R, 2),
            ),
        ),
        # if statement
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(2),
        ),
        instructions.core.LoadInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(
                address=Address(0),
                index=Register(RegisterName.R, 1),
            ),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(0),
        ),
        instructions.core.BneInstruction(
            reg0=Register(RegisterName.R, 0),
            reg1=Register(RegisterName.R, 1),
            line=Immediate(28),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(2),
        ),
        instructions.core.LoadInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(
                address=Address(0),
                index=Register(RegisterName.R, 1),
            ),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(1),
        ),
        instructions.core.AddInstruction(
            regout=Register(RegisterName.R, 0),
            reg0=Register(RegisterName.R, 0),
            reg1=Register(RegisterName.R, 1),
        ),
        instructions.core.SetInstruction(
            reg=Register(RegisterName.R, 1),
            value=Immediate(2),
        ),
        instructions.core.StoreInstruction(
            reg=Register(RegisterName.R, 0),
            entry=ArrayEntry(
                address=Address(0),
                index=Register(RegisterName.R, 1),
            ),
        ),
        # return cmds
        instructions.core.RetArrInstruction(
            address=Address(0),
        ),
        instructions.core.RetArrInstruction(
            address=Address(1),
        ),
    ])
    for i, command in enumerate(subroutine.commands):
        print(repr(command))
        expected_command = expected.commands[i]
        print(repr(expected_command))
        print()
        assert command == expected_command
    print(subroutine)
    print(expected)
    assert subroutine == expected


if __name__ == "__main__":
    test_simple()
    test_rotations()
    test_epr()
    test_two_epr()
    test_epr_m()
