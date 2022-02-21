# Copyright 2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for :mod:`pennylane.operation`.
"""
import pytest
from collections import OrderedDict
from pennylane.wires import Wires
import pennylane.numpy as np
import pennylane as qml
from pennylane.transforms.commutation_dag import simplify


class TestCommutingFunction:
    """Commutation function tests."""

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1, 0]], False),
            ([[1, 0], [1, 0]], True),
            ([[0, 1], [2, 3]], True),
            ([[0, 1], [3, 1]], True),
        ],
    )
    def test_cnot(self, wires, res):
        """Commutation between two CNOTs."""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[0]), qml.CNOT(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[1, 2], [1, 0, 2]], True),
            ([[1, 2], [0, 1, 2]], True),
            ([[3, 2], [0, 1, 2]], True),
            ([[0, 1], [0, 1, 2]], False),
        ],
    )
    def test_cnot_toffoli(self, wires, res):
        """Commutation between CNOT and Toffoli"""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[0]), qml.Toffoli(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[1, 2], [1, 0]], True),
            ([[0, 1], [0, 1]], False),
            ([[0, 1], [2, 0]], True),
            ([[0, 1], [0, 2]], True),
        ],
    )
    def test_cnot_cz(self, wires, res):
        """Commutation between CNOT and CZ"""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[0]), qml.CZ(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0, 1, 2]], True),
            ([[0, 2], [0, 1, 2]], True),
            ([[0, 2], [0, 2, 1]], True),
        ],
    )
    def test_cz_mcz(self, wires, res):
        """Commutation between CZ and MCZ."""

        def z():
            qml.PauliZ(wires=wires[1][1])

        commutation = qml.is_commuting(
            qml.CZ(wires=wires[0]), qml.transforms.ctrl(z, control=wires[1][0])()
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0, 1, 2]], False),
            ([[0, 2], [0, 1, 2]], False),
            ([[0, 2], [0, 2, 1]], False),
            ([[0, 3], [0, 2, 1]], True),
            ([[0, 3], [1, 2, 0]], True),
        ],
    )
    def test_cnot_mcz(self, wires, res):
        """Commutation between CNOT and MCZ."""

        def z():
            qml.PauliZ(wires=wires[1][2])

        commutation = qml.is_commuting(
            qml.CNOT(wires=wires[0]), qml.transforms.ctrl(z, control=wires[1][:-1])()
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[1], [0, 1]], True),
            ([[0], [0, 1]], False),
            ([[2], [0, 1]], True),
        ],
    )
    def test_x_cnot(self, wires, res):
        """Commutation between PauliX and CNOT."""
        commutation = qml.is_commuting(qml.PauliX(wires=wires[0]), qml.CNOT(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[1], [0, 1]], True),
            ([[0], [0, 1]], False),
            ([[2], [0, 1]], True),
        ],
    )
    def test_cnot_x(self, wires, res):
        """Commutation between CNOT and PauliX."""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[1]), qml.PauliX(wires=wires[0]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[1], [0, 1]], False),
            ([[0], [0, 1]], False),
            ([[2], [0, 1]], True),
        ],
    )
    def test_x_cy(self, wires, res):
        """Commutation between PauliX and CY."""
        commutation = qml.is_commuting(qml.PauliX(wires=wires[0]), qml.CY(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 2], [0, 1, 2]], False),
            ([[0, 1], [0, 1, 2]], False),
            ([[0, 3], [0, 1, 2]], True),
            ([[1, 2], [0, 1, 2]], False),
        ],
    )
    def test_cnot_cswap(self, wires, res):
        """Commutation between CNOT and CSWAP."""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[0]), qml.CSWAP(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1, 2], [1, 2]], False),
        ],
    )
    def test_cswap_cnot(self, wires, res):
        """Commutation between CSWAP and CNOT."""
        commutation = qml.is_commuting(qml.CSWAP(wires=wires[0]), qml.CNOT(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1, 2], [2, 1, 0]], False),
        ],
    )
    def test_cswap_cswap(self, wires, res):
        """Commutation between CSWAP and CSWAP."""
        commutation = qml.is_commuting(qml.CSWAP(wires=wires[0]), qml.CSWAP(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0, 1]], False),
        ],
    )
    def test_cnot_swap(self, wires, res):
        """Commutation between CNOT and SWAP."""
        commutation = qml.is_commuting(qml.CNOT(wires=wires[0]), qml.SWAP(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0, 1]], False),
        ],
    )
    def test_swap_cnot(self, wires, res):
        """Commutation between SWAP and CNOT."""
        commutation = qml.is_commuting(qml.SWAP(wires=wires[0]), qml.CNOT(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 2], [0, 1, 2]], False),
            ([[0, 1], [0, 1, 2]], False),
            ([[0, 3], [0, 1, 2]], True),
        ],
    )
    def test_cz_cswap(self, wires, res):
        """Commutation between CZ and CSWAP."""
        commutation = qml.is_commuting(qml.CZ(wires=wires[0]), qml.CSWAP(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 2], [0, 1, 2, 3]], False),
            ([[0, 1], [0, 1, 2, 3]], False),
            ([[0, 3], [0, 1, 2, 3]], True),
        ],
    )
    def test_cnot_multicx(self, wires, res):
        """Commutation between CNOT and MultiControlledX."""
        commutation = qml.is_commuting(
            qml.CNOT(wires=wires[0]),
            qml.MultiControlledX(
                control_wires=wires[1][0:3], wires=wires[1][-1], control_values="111"
            ),
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_cphase_z(self, wires, res):
        """Commutation between CPhase and PauliZ."""
        commutation = qml.is_commuting(qml.CPhase(0.2, wires=wires[0]), qml.PauliZ(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_cphase_phase(self, wires, res):
        """Commutation between CPhase and Phase."""
        commutation = qml.is_commuting(
            qml.CPhase(0.2, wires=wires[0]), qml.PhaseShift(0.1, wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], False),
            ([[0, 1], [1]], False),
        ],
    )
    def test_cphase_paulix(self, wires, res):
        """Commutation between CPhase and PauliX."""
        commutation = qml.is_commuting(qml.CPhase(0.2, wires=wires[0]), qml.PauliX(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_cphase_zero_paulix(self, wires, res):
        """Commutation between CPhase(0.0) and PauliX."""
        commutation = qml.is_commuting(qml.CPhase(0.0, wires=wires[0]), qml.PauliX(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], False),
        ],
    )
    def test_crx_pauliz(self, wires, res):
        """Commutation between CRX(0.1) and PauliZ."""
        commutation = qml.is_commuting(qml.CRX(0.1, wires=wires[0]), qml.PauliZ(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_crx_zero_pauliz(self, wires, res):
        """Commutation between CRX(0.0) and PauliZ."""
        commutation = qml.is_commuting(qml.CRX(0.0, wires=wires[0]), qml.PauliZ(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], False),
            ([[0, 1], [1]], False),
        ],
    )
    def test_crz_paulix(self, wires, res):
        """Commutation between CRZ(0.1) and PauliX."""
        commutation = qml.is_commuting(qml.CRZ(0.1, wires=wires[0]), qml.PauliX(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_crz_zero_paulix(self, wires, res):
        """Commutation between CRZ(0.0) and PauliX."""
        commutation = qml.is_commuting(qml.CRZ(0.0, wires=wires[0]), qml.PauliX(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], False),
            ([[0, 1], [1]], False),
        ],
    )
    def test_cry_hadamard(self, wires, res):
        """Commutation between CRY(0.1) and Hadamard."""
        commutation = qml.is_commuting(qml.CRY(0.1, wires=wires[0]), qml.Hadamard(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], True),
            ([[0, 1], [1]], True),
        ],
    )
    def test_cry_zero_hadamard(self, wires, res):
        """Commutation between CRY(0.0) and Hadamard."""
        commutation = qml.is_commuting(qml.CRY(0.0, wires=wires[0]), qml.Hadamard(wires=wires[1]))
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_rot_x_simplified(self, wires, res):
        """Commutation between Rot(np.pi / 2, 0.1, -np.pi / 2) and PauliX."""
        commutation = qml.is_commuting(
            qml.Rot(np.pi / 2, 0.1, -np.pi / 2, wires=wires[0]), qml.PauliX(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_rot_y_simplified(self, wires, res):
        """Commutation between Rot(0, 0.1, 0) and PauliY."""
        commutation = qml.is_commuting(
            qml.Rot(0, 0.1, 0, wires=wires[0]), qml.PauliY(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_rot_z_simplified(self, wires, res):
        """Commutation between Rot(0.1, 0.0, 0.2) and PauliZ."""
        commutation = qml.is_commuting(
            qml.Rot(0.1, 0, 0.2, wires=wires[0]), qml.PauliZ(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_rot_hadamard_simplified(self, wires, res):
        """Commutation between Rot(np.pi, np.pi / 2, 0) and Hadamard."""
        commutation = qml.is_commuting(
            qml.Rot(np.pi, np.pi / 2, 0, wires=wires[0]), qml.Hadamard(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], False),
            ([[0], [1]], True),
        ],
    )
    def test_rot_z(self, wires, res):
        """Commutation between Rot(0.1, 0.2, 0.3) and PauliZ."""
        commutation = qml.is_commuting(
            qml.Rot(0.1, 0.2, 0.3, wires=wires[0]), qml.PauliZ(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1]], True),
            ([[0, 1], [0]], False),
        ],
    )
    def test_crot_x_simplified(self, wires, res):
        """Commutation between CRot(np.pi / 2, 0.1, -np.pi / 2) and PauliX."""
        commutation = qml.is_commuting(
            qml.CRot(np.pi / 2, 0.1, -np.pi / 2, wires=wires[0]), qml.PauliX(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1]], True),
            ([[0, 1], [0]], False),
        ],
    )
    def test_crot_y_simplified(self, wires, res):
        """Commutation between CRot(0, 0.1, 0) and PauliY."""
        commutation = qml.is_commuting(
            qml.CRot(0, 0.1, 0, wires=wires[0]), qml.PauliY(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1]], True),
            ([[0, 1], [0]], True),
        ],
    )
    def test_crot_z_simplified(self, wires, res):
        """Commutation between CRot(0.1, 0, 0.2) and PauliZ."""
        commutation = qml.is_commuting(
            qml.CRot(0.1, 0, 0.2, wires=wires[0]), qml.PauliZ(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1]], True),
            ([[0, 1], [0]], False),
        ],
    )
    def test_crot_hadamard_simplified(self, wires, res):
        """Commutation between CRot(np.pi, np.pi / 2, 0) and Hadamard."""
        commutation = qml.is_commuting(
            qml.CRot(np.pi, np.pi / 2, 0, wires=wires[0]), qml.Hadamard(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [1]], False),
            ([[0, 1], [0]], True),
        ],
    )
    def test_crot_z(self, wires, res):
        """Commutation between CRot(0.1, 0.2, 0.3) and PauliZ."""
        commutation = qml.is_commuting(
            qml.CRot(0.1, 0.2, 0.3, wires=wires[0]), qml.PauliZ(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_u2_y_simplified(self, wires, res):
        """Commutation between U2(2*np.pi, -2*np.pi) and PauliY."""
        commutation = qml.is_commuting(
            qml.U2(2 * np.pi, -2 * np.pi, wires=wires[0]), qml.PauliY(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_u2_x_simplified(self, wires, res):
        """Commutation between U2(np.pi/2, -np.pi/2) and PauliX."""
        commutation = qml.is_commuting(
            qml.U2(np.pi / 2, -np.pi / 2, wires=wires[0]), qml.PauliX(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], False),
            ([[0], [1]], True),
        ],
    )
    def test_u2_u2(self, wires, res):
        """Commutation between U2(0.1, 0.2) and U2(0.3, 0.1)."""
        commutation = qml.is_commuting(
            qml.U2(0.1, 0.2, wires=wires[0]), qml.U2(0.3, 0.1, wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], False),
            ([[0, 1], [1]], False),
        ],
    )
    def test_crot_u2(self, wires, res):
        """Commutation between CRot(0.1, 0.2, 0.3) and U2(0.4, 0.5)."""
        commutation = qml.is_commuting(
            qml.CRot(0.1, 0.2, 0.3, wires=wires[0]), qml.U2(0.4, 0.5, wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0]], False),
            ([[0, 1], [1]], False),
        ],
    )
    def test_u2_crot(self, wires, res):
        """Commutation between U2(0.1, 0.2) and CRot(0.3, 0.4, 0.5)."""
        commutation = qml.is_commuting(
            qml.U2(0.1, 0.2, wires=wires[1]), qml.CRot(0.3, 0.4, 0.5, wires=wires[0])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0, 1], [0, 1]], False),
            ([[0, 1], [1, 0]], False),
            ([[0, 2], [0, 1]], True),
            ([[0, 2], [1, 2]], False),
        ],
    )
    def test_crot_crot(self, wires, res):
        """Commutation between CRot(0.1, 0.2, 0.3) and CRot(0.3, 0.4, 0.5)."""
        commutation = qml.is_commuting(
            qml.CRot(0.1, 0.2, 0.3, wires=wires[1]), qml.CRot(0.3, 0.4, 0.5, wires=wires[0])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_u3_simplified_z(self, wires, res):
        """Commutation between U3(0.0, 0.1, 0.0) and PauliZ."""
        commutation = qml.is_commuting(
            qml.U3(0.0, 0.1, 0.0, wires=wires[1]), qml.PauliZ(wires=wires[0])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_u3_simplified_y(self, wires, res):
        """Commutation between U3(0.1, 0.0, 0.0) and PauliY."""
        commutation = qml.is_commuting(
            qml.U3(0.1, 0.0, 0.0, wires=wires[1]), qml.PauliY(wires=wires[0])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], True),
            ([[0], [1]], True),
        ],
    )
    def test_u3_simplified_x(self, wires, res):
        """Commutation between U3(0.1, -np.pi/2, np.pi/2) and PauliX."""
        commutation = qml.is_commuting(
            qml.U3(0.1, -np.pi / 2, np.pi / 2, wires=wires[0]), qml.PauliX(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], False),
            ([[0], [1]], True),
        ],
    )
    def test_u3_rot(self, wires, res):
        """Commutation between U3(0.1, 0.2, 0.3) and Rot(0.3, 0.2, 0.1)."""
        commutation = qml.is_commuting(
            qml.U3(0.1, 0.2, 0.3, wires=wires[0]), qml.Rot(0.3, 0.2, 0.1, wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], False),
            ([[0], [1]], True),
        ],
    )
    def test_u3_identity_barrier(self, wires, res):
        """Commutation between U3(0.0, 0.0, 0.0) and Barrier."""
        commutation = qml.is_commuting(
            qml.U3(0.0, 0.0, 0.0, wires=wires[0]), qml.Barrier(wires=wires[1])
        )
        assert commutation == res

    @pytest.mark.parametrize(
        "wires,res",
        [
            ([[0], [0]], False),
            ([[0], [1]], True),
        ],
    )
    def test_u3_identity_barrier(self, wires, res):
        """Commutation between Barrier and U3(0.0, 0.0, 0.0)."""
        commutation = qml.is_commuting(
            qml.Barrier(wires=wires[1]), qml.U3(0.0, 0.0, 0.0, wires=wires[0])
        )
        assert commutation == res

    def test_simplify_not_roations(self):
        """Test that the simplify function returns a warning when giving a non rotation operation as argument."""
        id = qml.Identity(wires=0)

        with pytest.raises(
            qml.QuantumFunctionError, match="Identity is not a Rot, U2, U3 or CRot."
        ):
            simplify(id)

    def test_operation_1_not_supported(self):
        """Test that giving a non supported operation raises an error."""
        rho = np.zeros((2**1, 2**1), dtype=np.complex128)
        rho[0, 0] = 1
        with pytest.raises(
            qml.QuantumFunctionError, match="Operation QubitDensityMatrix not supported."
        ):
            qml.is_commuting(qml.QubitDensityMatrix(rho, wires=[0]), qml.PauliX(wires=0))

    def test_operation_2_not_supported(self):
        """Test that giving a non supported operation raises an error."""

        with pytest.raises(qml.QuantumFunctionError, match="Operation PauliRot not supported."):
            qml.is_commuting(qml.PauliX(wires=0), qml.PauliRot(1, "X", wires=0))


    def test_operation_1_multiple_targets(self):
        """Test that giving a multiple target controlled operation raises an error."""

        def op():
            qml.PauliZ(wires=2)
            qml.PauliY(wires=2)

        with pytest.raises(
            qml.QuantumFunctionError, match="MultipleTargets controlled is not supported."
        ):
            qml.is_commuting(qml.transforms.ctrl(op, control=[0, 1])(), qml.PauliX(wires=0))

    def test_operation_2_multiple_targets(self):
        """Test that giving a multiple target controlled operation raises an error."""

        def op():
            qml.PauliZ(wires=2)
            qml.PauliY(wires=2)

        with pytest.raises(
            qml.QuantumFunctionError, match="MultipleTargets controlled is not supported."
        ):
            qml.is_commuting(qml.PauliX(wires=0), qml.transforms.ctrl(op, control=[0, 1])())

    def test_non_commuting(self):
        """Test the function with an operator from the non-commuting list."""

        res = qml.is_commuting(qml.PauliX(wires=0), qml.QFT(wires=[1, 0]))
        assert res == False


class TestCommutationDAG:
    """Commutation DAG tests."""

    def test_return_dag(self):
        def circuit():
            qml.PauliZ(wires=0)

        dag_object = qml.transforms.commutation_dag(circuit)()
        dag = dag_object.graph

        assert len(dag) != 0

    def test_dag_invalid_argument(self):
        """Assert error raised when input is neither a tape, QNode, nor quantum function"""

        with pytest.raises(ValueError, match="Input is not a tape, QNode, or quantum function"):
            qml.transforms.commutation_dag(qml.PauliZ(0))()

    def test_dag_wrong_function(self):
        """Assert error raised when input function is not a quantum function"""

        def test_function(x):
            return x

        with pytest.raises(ValueError, match="Function contains no quantum operation"):
            qml.transforms.commutation_dag(test_function)(1)

    def test_dag_transform_simple_dag_function(self):
        """Test a simple DAG on 1 wire with a quantum function."""

        def circuit():
            qml.PauliZ(wires=0)
            qml.PauliX(wires=0)

        dag = qml.transforms.commutation_dag(circuit)()

        a = qml.PauliZ(wires=0)
        b = qml.PauliX(wires=0)

        nodes = [a, b]
        edges = [(0, 1, {"commute": False})]

        assert dag.get_node(0).op.compare(a)
        assert dag.get_node(1).op.compare(b)
        assert dag.get_edge(0, 1) == {0: {"commute": False}}
        assert dag.get_edge(0, 2) is None
        assert dag.observables == []
        for i, node in enumerate(dag.get_nodes()):
            assert node[1].op.compare(nodes[i])
        for i, edge in enumerate(dag.get_edges()):
            assert edges[i] == edge

    def test_dag_transform_simple_dag_tape(self):
        """Test a simple DAG on 1 wire with a quantum tape."""
        with qml.tape.QuantumTape() as tape:
            qml.PauliZ(wires=0)
            qml.PauliX(wires=0)

        dag = qml.transforms.commutation_dag(tape)()

        a = qml.PauliZ(wires=0)
        b = qml.PauliX(wires=0)

        nodes = [a, b]
        edges = [(0, 1, {"commute": False})]

        assert dag.get_node(0).op.compare(a)
        assert dag.get_node(1).op.compare(b)
        assert dag.get_edge(0, 1) == {0: {"commute": False}}
        assert dag.get_edge(0, 2) is None
        assert dag.observables == []
        for i, node in enumerate(dag.get_nodes()):
            assert node[1].op.compare(nodes[i])
        for i, edge in enumerate(dag.get_edges()):
            assert edges[i] == edge

    def test_dag_transform_simple_dag_function_custom_wire(self):
        """Test a simple DAG on 2 wires with a quantum function and custom wires."""

        def circuit():
            qml.PauliZ(wires="a")
            qml.PauliX(wires="c")

        dag = qml.transforms.commutation_dag(circuit)()

        a = qml.PauliZ(wires=0)
        b = qml.PauliX(wires=1)

        nodes = [a, b]
        edges = [(0, 1, {"commute": False})]

        assert dag.get_node(0).op.compare(a)
        assert dag.get_node(1).op.compare(b)
        assert dag.get_edge(0, 1) is None
        assert dag.get_edge(0, 2) is None
        assert dag.observables == []
        for i, node in enumerate(dag.get_nodes()):
            assert node[1].op.compare(nodes[i])
        for i, edge in enumerate(dag.get_edges()):
            assert edges[i] == edge

    def test_dag_transform_simple_dag_qnode(self):
        """Test a simple DAG on 1 wire with a qnode."""

        dev = qml.device("default.qubit", wires=1)

        @qml.qnode(dev)
        def circuit():
            qml.PauliZ(wires=0)
            qml.PauliX(wires=0)
            return qml.expval(qml.PauliX(wires=0))

        dag = qml.transforms.commutation_dag(circuit)()

        a = qml.PauliZ(wires=0)
        b = qml.PauliX(wires=0)

        nodes = [a, b]
        edges = [(0, 1, {"commute": False})]

        assert dag.get_node(0).op.compare(a)
        assert dag.get_node(1).op.compare(b)
        assert dag.get_edge(0, 1) == {0: {"commute": False}}
        assert dag.get_edge(0, 2) is None
        assert dag.observables[0].return_type.__repr__() == "expval"
        assert dag.observables[0].name == "PauliX"
        assert dag.observables[0].wires.tolist() == [0]
        for i, node in enumerate(dag.get_nodes()):
            assert node[1].op.compare(nodes[i])
        for i, edge in enumerate(dag.get_edges()):
            assert edges[i] == edge

    def test_dag_pattern(self):
        "Test a the DAG and its attributes for a more complicated circuit."

        def circuit():
            qml.CNOT(wires=[3, 0])
            qml.PauliX(wires=4)
            qml.PauliZ(wires=0)
            qml.CNOT(wires=[4, 2])
            qml.CNOT(wires=[0, 1])
            qml.CNOT(wires=[3, 4])
            qml.CNOT(wires=[1, 2])
            qml.PauliX(wires=1)
            qml.CNOT(wires=[1, 0])
            qml.PauliX(wires=1)
            qml.CNOT(wires=[1, 2])
            qml.CNOT(wires=[0, 3])

        dag = qml.transforms.commutation_dag(circuit)()

        wires = [3, 0, 4, 2, 1]
        consecutive_wires = Wires(range(len(wires)))
        wires_map = OrderedDict(zip(wires, consecutive_wires))

        nodes = [
            qml.CNOT(wires=[3, 0]),
            qml.PauliX(wires=4),
            qml.PauliZ(wires=0),
            qml.CNOT(wires=[4, 2]),
            qml.CNOT(wires=[0, 1]),
            qml.CNOT(wires=[3, 4]),
            qml.CNOT(wires=[1, 2]),
            qml.PauliX(wires=1),
            qml.CNOT(wires=[1, 0]),
            qml.PauliX(wires=1),
            qml.CNOT(wires=[1, 2]),
            qml.CNOT(wires=[0, 3]),
        ]

        for node in nodes:
            node._wires = Wires([wires_map[wire] for wire in node.wires.tolist()])

        edges = [
            (0, 2, {"commute": False}),
            (0, 4, {"commute": False}),
            (1, 3, {"commute": False}),
            (2, 8, {"commute": False}),
            (3, 5, {"commute": False}),
            (4, 6, {"commute": False}),
            (5, 11, {"commute": False}),
            (6, 7, {"commute": False}),
            (7, 8, {"commute": False}),
            (8, 9, {"commute": False}),
            (8, 11, {"commute": False}),
            (9, 10, {"commute": False}),
        ]

        direct_successors = [[2, 4], [3], [8], [5], [6], [11], [7], [8], [9, 11], [10], [], []]
        successors = [
            [2, 4, 6, 7, 8, 9, 10, 11],
            [3, 5, 11],
            [8, 9, 10, 11],
            [5, 11],
            [6, 7, 8, 9, 10, 11],
            [11],
            [7, 8, 9, 10, 11],
            [8, 9, 10, 11],
            [9, 10, 11],
            [10],
            [],
            [],
        ]
        direct_predecessors = [[], [], [0], [1], [0], [3], [4], [6], [2, 7], [8], [9], [5, 8]]
        predecessors = [
            [],
            [],
            [0],
            [1],
            [0],
            [1, 3],
            [0, 4],
            [0, 4, 6],
            [0, 2, 4, 6, 7],
            [0, 2, 4, 6, 7, 8],
            [0, 2, 4, 6, 7, 8, 9],
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
        ]

        assert dag.observables == []

        for i in range(0, 12):
            assert dag.get_node(i).op.name == nodes[i].name
            assert dag.get_node(i).op.wires == nodes[i].wires
            assert dag.direct_successors(i) == direct_successors[i]
            assert dag.get_node(i).successors == successors[i] == dag.successors(i)
            assert dag.direct_predecessors(i) == direct_predecessors[i]
            assert dag.get_node(i).predecessors == predecessors[i] == dag.predecessors(i)

        for i, edge in enumerate(dag.get_edges()):
            assert edges[i] == edge
