import enum
from collections import Counter
from typing import List, Union, Iterable


@enum.unique
class State(enum.IntFlag):
    low = 0
    high = 1
    z = 2

    def __eq__(self, other):
        if isinstance(other, Node):
            return int(self) == int(other.state)

        if not isinstance(other, State):
            raise ValueError(
                f"Cannot compare {other.__class__.__name__} class with a State class."
            )

        return int(self) == int(other)


class Node:
    _id_counter: int = 1

    def __init__(self, state: State = State.low, name: str = None):
        self.state = state
        Node._id_counter += 1
        if name:
            self.name = name
        else:
            self.name = f"Node{Node._id_counter}"

    def __str__(self):
        return f"{self.name}: {str(self.state)}"


class NamedObjectList(list):
    object_type_name = "Object"

    def __getitem__(self, index):
        if isinstance(index, int):
            return super().__getitem__(index)
        return self.get_object_by_name(index)

    def get_object_by_name(self, name: str) -> Node:
        for n in self:
            if n.name == name:
                return n
        raise ValueError(
            f'{self.object_type_name} {name} not found. Valid node names are ({", ".join(i.name for i in self)})'
        )


class ComponentList(NamedObjectList):
    object_type_name = "Component"
    pass


class NodeList(NamedObjectList):
    object_type_name = "Node"

    def validate(
        self,
        element_name: str,
        expected_names: List[str] = None,
        min_length=None,
        max_length=None,
    ):
        if min_length and len(self) < min_length:
            raise ValueError(
                f"{element_name} must have a minimum of {min_length} inputs."
            )

        if max_length and len(self) > max_length:
            raise ValueError(
                f"{element_name} must have a maximum of {max_length} inputs."
            )

        if expected_names:
            unexpected_names = set(i.name for i in self).difference(expected_names)
            if len(unexpected_names) > 0:
                raise ValueError(
                    f'The following node names were not expected: {", ".join(i for i in unexpected_names)}'
                )

            missing_names = set(expected_names).difference(i.name for i in self)
            if len(missing_names) > 0:
                raise ValueError(
                    f'The following node names were missing: {", ".join(i for i in missing_names)}'
                )

    def __str__(self):
        return f'[{", ".join([str(i) for i in self])}]'


class ComponentBase:
    _inputs = NotImplemented
    _outputs = NotImplemented
    components: Iterable = None
    _components: ComponentList = None

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        if self.components:
            if isinstance(self.components, (list, tuple)):
                self._components = ComponentList(
                    [i() if i.__class__ is type else i for i in self.components]
                )
            else:
                raise ValueError('components variable must be set to a list or tuple.')

        else:
            c = self.get_components()
            if isinstance(c, ComponentList):
                self._components = c
            elif isinstance(c, (list, tuple)):
                self._components = ComponentList(c)
            else:
                raise ValueError('get_components() must return a ComponentList, list or tuple.')
        self.name = name
        if inputs:
            self.set_inputs(inputs)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        if name is None:
            name = f"{self.__class__.__name__}"
        self._name = name

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        self._inputs = inputs

    def get_components(self):
        return list()


class OneOutputComponent(ComponentBase):
    _output: Node = None

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        out_name = f"{name}_out" if name else None
        if not self._output:
            self._output = Node(name=out_name)

    def calculate(self):
        for c in self._components:
            c.calculate()
        return self.output_node.state

    @property
    def output_node(self):
        return self._output

    def __str__(self):
        return f'{self.name}: ({", ".join([str(i) for i in self._inputs])}) -> ({str(self._output)})'


class MinTwoInputOneOutputComponent(OneOutputComponent):
    def set_inputs(self, inputs: Union[NodeList, list]):
        if inputs and len(inputs) < 2:
            raise ValueError(f"{self.__class__.__name__} must have two or more inputs.")
        super().set_inputs(inputs)


class MultipleOutputComponent(ComponentBase):
    _outputs: NodeList = None

    def calculate(self):
        for c in self._components:
            c.calculate()
        return self.output_nodes

    @property
    def output_nodes(self) -> NodeList:
        return self._outputs

    def __str__(self):
        return (
            f'{self.name}: ({", ".join([str(i) for i in self._inputs])}) -> '
            f'({", ".join([str(i) for i in self._outputs])})'
        )


class OrGate(MinTwoInputOneOutputComponent):
    def calculate(self):
        self._output.state = (
            State.high
            if any(i.state >= State.high for i in self._inputs)
            else State.low
        )
        return self._output.state


class AndGate(MinTwoInputOneOutputComponent):
    def calculate(self):
        self._output.state = (
            State.high
            if all(i.state >= State.high for i in self._inputs)
            else State.low
        )
        return self._output.state


class NotGate(OneOutputComponent):
    def set_inputs(self, inputs: Union[NodeList, list]):
        if len(inputs) != 1:
            raise ValueError("A not gate can only have one input.")
        # Skip MinTwoInputOneOutputComponent.set_inputs and execute ComponentBase.set_inputs instead
        super().set_inputs(inputs)

    def calculate(self):
        self._output.state = State.high if self._inputs[0] == State.low else State.low
        return self._output.state


class NorGate(MinTwoInputOneOutputComponent):
    components = (OrGate, NotGate)

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        self._output = self._components["NotGate"].output_node

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        or_gate = self._components["OrGate"]
        not_gate = self._components["NotGate"]
        or_gate.set_inputs(inputs)
        not_gate.set_inputs([or_gate.output_node])


class NandGate(MinTwoInputOneOutputComponent):
    components = (AndGate, NotGate)

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        self._output = self._components["NotGate"].output_node

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        and_gate = self._components["AndGate"]
        not_gate = self._components["NotGate"]
        and_gate.set_inputs(inputs)
        not_gate.set_inputs([and_gate.output_node])


class XorGate(MinTwoInputOneOutputComponent):
    def calculate(self):
        converted_inputs = [i.state >= State.high for i in self._inputs]
        result = Counter(converted_inputs)
        self._output.state = State.high if result.get(True) == 1 else State.low
        return self._output.state


class XnorGate(MinTwoInputOneOutputComponent):
    components = (XorGate, NotGate)

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        self._output = self._components["NotGate"].output_node

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        xor_gate = self._components["XorGate"]
        not_gate = self._components["NotGate"]
        xor_gate.set_inputs(inputs)
        not_gate.set_inputs([xor_gate.output_node])


class SRNorLatch(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self.components = (NorGate(name="NorGate1"), NorGate(name="NorGate2"))
        super().__init__(inputs, name)
        self._outputs = NodeList([i.output_node for i in self._components])

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(
            self.name, expected_names=["Set", "Reset"], min_length=2, max_length=2
        )

        super().set_inputs(inputs)
        nor_gate1 = self._components["NorGate1"]
        nor_gate2 = self._components["NorGate2"]
        nor_gate1.set_inputs(
            [inputs.get_object_by_name("Reset"), nor_gate2.output_node]
        )
        nor_gate2.set_inputs([inputs.get_object_by_name("Set"), nor_gate1.output_node])
        nor_gate1.output_node.name = f"Q"
        nor_gate2.output_node.name = f"QBar"
        self._outputs = NodeList([nor_gate1.output_node, nor_gate2.output_node])

    def calculate(self):
        self._components["NorGate1"].calculate()
        self._components["NorGate2"].calculate()
        self._components["NorGate1"].calculate()
        return self.output_nodes

    def __str__(self):
        return f'({self._inputs["Reset"]},{self._inputs["Set"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


class SRNandLatch(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        self._outputs = NodeList([i.output_node for i in self._components])

    def get_components(self):
        return (NandGate(name="NandGate1"), NandGate(name="NandGate2"))

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(
            self.name, expected_names=["Set", "Reset"], min_length=2, max_length=2
        )

        super().set_inputs(inputs)
        gate1 = self._components["NandGate1"]
        gate2 = self._components["NandGate2"]
        gate1.set_inputs([inputs.get_object_by_name("Set"), gate2.output_node])
        gate2.set_inputs([inputs.get_object_by_name("Reset"), gate1.output_node])
        gate1.output_node.name = f"Q"
        gate2.output_node.name = f"QBar"
        self._outputs = NodeList([gate1.output_node, gate2.output_node])

    def calculate(self):
        self._components["NandGate1"].calculate()
        self._components["NandGate2"].calculate()
        self._components["NandGate1"].calculate()
        return self.output_nodes

    def __str__(self):
        return f'({self._inputs["Reset"]},{self._inputs["Set"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


class DTypeFlipFlop(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self.components = (
            NotGate(),
            NandGate(name="NandGate1"),
            NandGate(name="NandGate2"),
            SRNandLatch(),
        )
        super().__init__(inputs, name)
        self._outputs = self._components["SRNandLatch"].output_nodes

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(
            self.name, expected_names=["D", "Clk"], min_length=2, max_length=2
        )
        super().set_inputs(inputs)
        not_gate = self._components["NotGate"]
        not_gate.set_inputs([inputs["D"]])
        nand_set = self._components["NandGate1"]
        nand_set.set_inputs([inputs["D"], inputs["Clk"]])
        nand_set.output_node.name = "Set"
        nand_reset = self._components["NandGate2"]
        nand_reset.set_inputs([not_gate.output_node, inputs["Clk"]])
        nand_reset.output_node.name = "Reset"
        srnand = self._components["SRNandLatch"]
        srnand.set_inputs([nand_set.output_node, nand_reset.output_node])
        self._outputs = srnand.output_nodes

    def __str__(self):
        return f'({self._inputs["D"]},{self._inputs["Clk"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


class JKFlipFlop(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self.name = name
        self.components = (
            NandGate(name="NandGate1"),
            NandGate(name="NandGate2"),
            SRNandLatch(),
        )
        super().__init__(inputs, name)
        self._outputs = self._components["SRNandLatch"].output_nodes

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(
            self.name, expected_names=["J", "K", "Clk"], min_length=2, max_length=2
        )
        super().set_inputs(inputs)
        srnand = self._components["SRNandLatch"]
        nand_set = self._components["NandGate1"]
        nand_set.set_inputs([inputs["J"], inputs["Clk"], srnand.output_nodes["Qbar"]])
        nand_set.output_node.name = "Set"
        nand_reset = self._components["NandGate2"]
        nand_reset.set_inputs([inputs["K"], inputs["Clk"], srnand.output_nodes["Q"]])
        nand_reset.output_node.name = "Reset"
        srnand.set_inputs([nand_set.output_node, nand_reset.output_node])
        self._outputs = srnand.output_nodes

    def __str__(self):
        return (
            f'({self._inputs["J"]},{self._inputs["K"]},{self._inputs["Clk"]} ) -> '
            f'({self._outputs["Q"]}, {self._outputs["QBar"]})'
        )


def main():
    s = Node(State.low, name="S")
    r = Node(State.high, name="R")
    latch = SRNorLatch([s, r])
    latch.calculate()
    print(latch)

    s.state = State.high
    r.state = State.low
    latch.calculate()
    print(latch)

    pass


if __name__ == "__main__":
    main()
