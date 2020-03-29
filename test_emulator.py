import pytest
import emulate
from emulate import State, Node


class TwoInputMixin:
    def test_names(self):
        c = self.component([Node(State.low), Node(State.low)], name='testname')
        assert c.name == 'testname'
        assert c.output_node.name == 'testname_out'

    def test_one_input_fails_init(self):
        with pytest.raises(ValueError) as ex:
            self.component([Node(State.low)], name='testname')
        assert str(ex.value) == f'{self.component.__name__} must have two or more inputs.'

    def test_one_input_fails_set_inputs(self):
        with pytest.raises(ValueError) as ex:
            c = self.component(name='testname')
            c.set_inputs([Node(State.low)])
        assert str(ex.value) == f'{self.component.__name__} must have two or more inputs.'


class TestOrGate(TwoInputMixin):
    component = emulate.OrGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.high),
                (State.high, State.high, State.low, State.high),
                (State.high, State.low, State.high, State.high),
                (State.high, State.low, State.low, State.high),
                (State.low, State.high, State.high, State.high),
                (State.low, State.high, State.low, State.high),
                (State.low, State.low, State.high, State.high),
                (State.low, State.low, State.low, State.low),
        )
    )
    def test_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestNorGate(TwoInputMixin):
    component = emulate.NorGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.low),
                (State.high, State.high, State.low, State.low),
                (State.high, State.low, State.high, State.low),
                (State.high, State.low, State.low, State.low),
                (State.low, State.high, State.high, State.low),
                (State.low, State.high, State.low, State.low),
                (State.low, State.low, State.high, State.low),
                (State.low, State.low, State.low, State.high),
        )
    )
    def test_nor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestAndGate(TwoInputMixin):
    component = emulate.AndGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.high),
                (State.high, State.high, State.low, State.low),
                (State.high, State.low, State.high, State.low),
                (State.high, State.low, State.low, State.low),
                (State.low, State.high, State.high, State.low),
                (State.low, State.high, State.low, State.low),
                (State.low, State.low, State.high, State.low),
                (State.low, State.low, State.low, State.low),
        )
    )
    def test_and_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestNandGate(TwoInputMixin):
    component = emulate.NandGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.low),
                (State.high, State.high, State.low, State.high),
                (State.high, State.low, State.high, State.high),
                (State.high, State.low, State.low, State.high),
                (State.low, State.high, State.high, State.high),
                (State.low, State.high, State.low, State.high),
                (State.low, State.low, State.high, State.high),
                (State.low, State.low, State.low, State.high),
        )
    )
    def test_nand_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestXorGate(TwoInputMixin):
    component = emulate.XorGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.low),
                (State.high, State.high, State.low, State.low),
                (State.high, State.low, State.high, State.low),
                (State.high, State.low, State.low, State.high),
                (State.low, State.high, State.high, State.low),
                (State.low, State.high, State.low, State.high),
                (State.low, State.low, State.high, State.high),
                (State.low, State.low, State.low, State.low),
        )
    )
    def test_xor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestXnorGate(TwoInputMixin):
    component = emulate.XnorGate

    @pytest.mark.parametrize(
        'ina, inb, inc, result',
        (
                (State.high, State.high, State.high, State.high),
                (State.high, State.high, State.low, State.high),
                (State.high, State.low, State.high, State.high),
                (State.high, State.low, State.low, State.low),
                (State.low, State.high, State.high, State.high),
                (State.low, State.high, State.low, State.low),
                (State.low, State.low, State.high, State.low),
                (State.low, State.low, State.low, State.high),
        )
    )
    def test_xnor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate() == result
        assert c.output_node.state == result


class TestNotGate():
    component = emulate.NotGate

    @pytest.mark.parametrize(
        'ina, result',
        (
                (State.low, State.high),
                (State.high, State.low),
        )
    )
    def test_not_gate(self, ina, result):
        a = Node(ina)
        b = self.component([a])
        assert b.calculate() == result
        assert b.output_node.state == result

    def test_names(self):
        c = self.component([Node(State.low)], name='testname')
        assert c.name == 'testname'
        assert c.output_node.name == 'testname_out'
