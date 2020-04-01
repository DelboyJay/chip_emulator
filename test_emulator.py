import pytest
from emulate import (
    State,
    Node,
    NodeList,
    AndGate,
    OrGate,
    NotGate,
    NandGate,
    NorGate,
    XorGate,
    XnorGate,
    SRNorLatch,
    SRNandLatch,
    DTypeFlipFlop,
)


class TestNodeList:
    def test_validation_minimum_success(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        nodes.validate("element", min_length=2)

    def test_validation_minimum_fails(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        with pytest.raises(ValueError) as ex:
            nodes.validate("element", min_length=3)
        assert str(ex.value) == f"element must have a minimum of 3 inputs."

    def test_validation_maximum_success(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        nodes.validate("element", max_length=2)

    def test_validation_maximum_fails(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        with pytest.raises(ValueError) as ex:
            nodes.validate("element", max_length=1)
        assert str(ex.value) == f"element must have a maximum of 1 inputs."

    def test_validation_expected_names_success(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        nodes.validate("element", expected_names=["1", "2"])

    def test_validation_expected_names_not_expected(self):
        nodes = NodeList([Node(name="1"), Node(name="2")])
        with pytest.raises(ValueError) as ex:
            nodes.validate("element", expected_names=["2", "3"])
        assert str(ex.value) == f"The following node names were not expected: 1"

    def test_validation_expected_names_missing(self):
        nodes = NodeList([Node(name="2")])
        with pytest.raises(ValueError) as ex:
            nodes.validate("element", expected_names=["2", "3"])
        assert str(ex.value) == f"The following node names were missing: 3"

    def test_get_object_by_name_success(self):
        node1 = Node(name="set")
        node2 = Node(name="Reset")
        node3 = Node(name="3")
        nodes = NodeList([node1, node2, node3])
        assert nodes.get_object_by_name("set") == node1
        assert nodes.get_object_by_name("Reset") == node2
        assert nodes.get_object_by_name("3") == node3

    def test_get_object_by_name_fails(self):
        node1 = Node(name="1")
        node2 = Node(name="2")
        node3 = Node(name="3")
        nodes = NodeList([node1, node2, node3])
        with pytest.raises(ValueError) as ex:
            nodes.get_object_by_name("4")
        assert str(ex.value) == f"Node 4 not found. Valid node names are (1, 2, 3)"

    def test_get_object_by_name_fail_case_sensitive(self):
        node1 = Node(name="set")
        node2 = Node(name="2")
        node3 = Node(name="3")
        nodes = NodeList([node1, node2, node3])
        with pytest.raises(ValueError) as ex:
            nodes.get_object_by_name("Set")
        assert str(ex.value) == f"Node Set not found. Valid node names are (set, 2, 3)"


class TwoInputMixin:
    component = NotImplemented

    def test_name(self):
        c = self.component([Node(State.low), Node(State.low)], name="testname")
        assert c.name == "testname"

    def test_name_null(self):
        c = self.component([Node(State.low), Node(State.low)], name=None)
        assert c.name == self.component.__name__

    def test_one_input_fails_init(self):
        with pytest.raises(ValueError) as ex:
            self.component([Node(State.low)], name="testname")
        assert (
            str(ex.value) == f"{self.component.__name__} must have two or more inputs."
        )

    def test_one_input_fails_set_inputs(self):
        with pytest.raises(ValueError) as ex:
            c = self.component(name="testname")
            c.inputs = [Node(State.low)]
        assert (
            str(ex.value) == f"{self.component.__name__} must have two or more inputs."
        )


class TestOrGate(TwoInputMixin):
    component = OrGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.high),
            (State.high, State.high, State.low, State.high),
            (State.high, State.low, State.high, State.high),
            (State.high, State.low, State.low, State.high),
            (State.low, State.high, State.high, State.high),
            (State.low, State.high, State.low, State.high),
            (State.low, State.low, State.high, State.high),
            (State.low, State.low, State.low, State.low),
        ),
    )
    def test_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestNorGate(TwoInputMixin):
    component = NorGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.low),
            (State.high, State.high, State.low, State.low),
            (State.high, State.low, State.high, State.low),
            (State.high, State.low, State.low, State.low),
            (State.low, State.high, State.high, State.low),
            (State.low, State.high, State.low, State.low),
            (State.low, State.low, State.high, State.low),
            (State.low, State.low, State.low, State.high),
        ),
    )
    def test_nor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestAndGate(TwoInputMixin):
    component = AndGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.high),
            (State.high, State.high, State.low, State.low),
            (State.high, State.low, State.high, State.low),
            (State.high, State.low, State.low, State.low),
            (State.low, State.high, State.high, State.low),
            (State.low, State.high, State.low, State.low),
            (State.low, State.low, State.high, State.low),
            (State.low, State.low, State.low, State.low),
        ),
    )
    def test_and_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestNandGate(TwoInputMixin):
    component = NandGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.low),
            (State.high, State.high, State.low, State.high),
            (State.high, State.low, State.high, State.high),
            (State.high, State.low, State.low, State.high),
            (State.low, State.high, State.high, State.high),
            (State.low, State.high, State.low, State.high),
            (State.low, State.low, State.high, State.high),
            (State.low, State.low, State.low, State.high),
        ),
    )
    def test_nand_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestXorGate(TwoInputMixin):
    component = XorGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.low),
            (State.high, State.high, State.low, State.low),
            (State.high, State.low, State.high, State.low),
            (State.high, State.low, State.low, State.high),
            (State.low, State.high, State.high, State.low),
            (State.low, State.high, State.low, State.high),
            (State.low, State.low, State.high, State.high),
            (State.low, State.low, State.low, State.low),
        ),
    )
    def test_xor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestXnorGate(TwoInputMixin):
    component = XnorGate

    @pytest.mark.parametrize(
        "ina, inb, inc, result",
        (
            (State.high, State.high, State.high, State.high),
            (State.high, State.high, State.low, State.high),
            (State.high, State.low, State.high, State.high),
            (State.high, State.low, State.low, State.low),
            (State.low, State.high, State.high, State.high),
            (State.low, State.high, State.low, State.low),
            (State.low, State.low, State.high, State.low),
            (State.low, State.low, State.low, State.high),
        ),
    )
    def test_xnor_gate(self, ina, inb, inc, result):
        c = self.component([Node(ina), Node(inb), Node(inc)])
        assert c.calculate()[0].state == result
        assert c.outputs[0].state == result


class TestNotGate:
    component = NotGate

    @pytest.mark.parametrize(
        "ina, result", ((State.low, State.high), (State.high, State.low),)
    )
    def test_not_gate(self, ina, result):
        a = Node(ina)
        b = self.component([a])
        assert b.calculate()[0].state == result
        assert b.outputs[0].state == result

    def test_names(self):
        c = self.component([Node(State.low)], name="testname")
        assert c.name == "testname"
        assert c.outputs[0].name == "testname_out"


class TestSRNorLatch:
    @pytest.mark.parametrize(
        "s, r, q, qbar",
        (
            (State.high, State.high, State.low, State.low),  # illegal state
            (State.high, State.low, State.high, State.low),
            (State.low, State.high, State.low, State.high),
            (State.low, State.low, State.high, State.low),  # Last state
        ),
    )
    def test_gate(self, s, r, q, qbar):
        latch = SRNorLatch([Node(s, name="Set"), Node(r, name="Reset")])
        out_nodes = latch.calculate()
        assert [i.state for i in out_nodes] == [q, qbar], latch

    def test_last_state(self):
        """
        Tests that Set=low & Reset=Low provides the previous state
        """
        set_node = Node(State.low, name="Set")
        reset_node = Node(State.high, name="Reset")
        latch = SRNorLatch([set_node, reset_node])
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.low
        assert out_nodes["QBar"] == State.high

        set_node.state = State.low
        reset_node.state = State.low
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.low
        assert out_nodes["QBar"] == State.high

        set_node.state = State.high
        reset_node.state = State.low
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.high
        assert out_nodes["QBar"] == State.low

        set_node.state = State.low
        reset_node.state = State.low
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.high
        assert out_nodes["QBar"] == State.low


class TestSRNandLatch:
    @pytest.mark.parametrize(
        "s, r, q, qbar",
        (
            (State.high, State.high, State.high, State.low),  # Last state
            (State.high, State.low, State.low, State.high),
            (State.low, State.high, State.high, State.low),
            (State.low, State.low, State.high, State.high),  # illegal state
        ),
    )
    def test_gate(self, s, r, q, qbar):
        latch = SRNandLatch([Node(s, name="Set"), Node(r, name="Reset")])
        out_nodes = latch.calculate()
        assert [i.state for i in out_nodes] == [q, qbar], latch

    def test_last_state(self):
        """
        Tests that Set=low & Reset=Low provides the previous state
        """
        set_node = Node(State.low, name="Set")
        reset_node = Node(State.high, name="Reset")
        latch = SRNandLatch([set_node, reset_node])
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.high
        assert out_nodes["QBar"] == State.low

        set_node.state = State.high
        reset_node.state = State.high
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.high
        assert out_nodes["QBar"] == State.low

        set_node.state = State.high
        reset_node.state = State.low
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.low
        assert out_nodes["QBar"] == State.high

        set_node.state = State.high
        reset_node.state = State.high
        out_nodes = latch.calculate()
        assert out_nodes["Q"] == State.low
        assert out_nodes["QBar"] == State.high


class TestDTypeFlipFlop:
    def test_basic(self):
        d = Node(State.low, name="D")
        clk = Node(State.high, name="Clk")
        ff = DTypeFlipFlop([d, clk])
        ff.calculate()
        assert ff.outputs["Q"].state == State.low
        assert ff.outputs["QBar"].state == State.high

        d.state = State.high
        clk.state = State.high
        ff.calculate()
        assert ff.outputs["Q"].state == State.high
        assert ff.outputs["QBar"].state == State.low

    def test_no_change_state_low_output(self):
        d = Node(State.low, name="D")
        clk = Node(State.high, name="Clk")
        ff = DTypeFlipFlop([d, clk])
        ff.calculate()
        assert ff.outputs["Q"].state == State.low
        assert ff.outputs["QBar"].state == State.high

        d.state = State.low
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.low
        assert ff.outputs["QBar"].state == State.high

        d.state = State.high
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.low
        assert ff.outputs["QBar"].state == State.high

        d.state = State.low
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.low
        assert ff.outputs["QBar"].state == State.high

    def test_no_change_state_high_output(self):
        d = Node(State.high, name="D")
        clk = Node(State.high, name="Clk")
        ff = DTypeFlipFlop([d, clk])
        ff.calculate()
        assert ff.outputs["Q"].state == State.high
        assert ff.outputs["QBar"].state == State.low

        d.state = State.low
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.high
        assert ff.outputs["QBar"].state == State.low

        d.state = State.high
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.high
        assert ff.outputs["QBar"].state == State.low

        d.state = State.low
        clk.state = State.low
        ff.calculate()
        assert ff.outputs["Q"].state == State.high
        assert ff.outputs["QBar"].state == State.low
