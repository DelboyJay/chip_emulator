import enum
from collections import Counter
from typing import List, Union


@enum.unique
class State(enum.IntFlag):
    low = 0
    high = 1
    z = 2

    def __eq__(self, other):
        if isinstance(other, Node):
            return int(self) == int(other.state)

        if not isinstance(other, State):
            raise ValueError(f'Cannot compare {other.__class__.__name__} class with a State class.')

        return int(self) == int(other)


class Node:
    _id_counter: int = 1

    def __init__(self, state: State = State.low, name: str = None):
        self.state = state
        Node._id_counter += 1
        if name:
            self.name = name
        else:
            self.name = f'Node{Node._id_counter}'

    def __str__(self):
        return f'{self.name}: {str(self.state)}'


class NodeList(list):
    def __getitem__(self, index):
        if isinstance(index, int):
            return super().__getitem__(index)
        return self.get_node_by_name(index)

    def get_node_by_name(self, name: str) -> Node:
        for n in self:
            if n.name == name:
                return n
        raise ValueError(f'Node {name} not found. Valid node names are ({", ".join(i.name for i in self)})')

    def validate(self, element_name: str, expected_names: List[str] = None, min_length=None, max_length=None):
        if min_length and len(self) < min_length:
            raise ValueError(f'{element_name} must have a minimum of {min_length} inputs.')

        if max_length and len(self) > max_length:
            raise ValueError(f'{element_name} must have a maximum of {max_length} inputs.')

        if expected_names:
            unexpected_names = set(i.name for i in self).difference(expected_names)
            if len(unexpected_names) > 0:
                raise ValueError(
                    f'The following node names were not expected: {", ".join(i for i in unexpected_names)}')

            missing_names = set(expected_names).difference(i.name for i in self)
            if len(missing_names) > 0:
                raise ValueError(f'The following node names were missing: {", ".join(i for i in missing_names)}')

    def __str__(self):
        return f'[{", ".join([str(i) for i in self])}]'


class ComponentMixin:
    _components: List = NotImplemented
    _inputs: NodeList = NotImplemented
    _name: str = None

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        if inputs:
            self.set_inputs(inputs)
        if name is None:
            name = f'{self.__class__.__name__}'
        self._name = name

    @property
    def name(self):
        return self._name

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        self._inputs = inputs


class MinTwoInputComponentMixin:
    def set_inputs(self, inputs: Union[NodeList, list]):
        if inputs and len(inputs) < 2:
            raise ValueError(f'{self.__class__.__name__} must have two or more inputs.')
        super().set_inputs(inputs)


class OneOutputComponent(ComponentMixin):
    _output: Node = None

    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        super().__init__(inputs, name)
        out_name = f'{name}_out' if name else None
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


class MultipleOutputComponent(ComponentMixin):
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


class OrGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        self._output.state = State.high if any(i.state >= State.high for i in self._inputs) else State.low
        return self._output.state


class AndGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        self._output.state = State.high if all(i.state >= State.high for i in self._inputs) else State.low
        return self._output.state


class NotGate(OneOutputComponent):
    def set_inputs(self, inputs: Union[NodeList, list]):
        if len(inputs) != 1:
            raise ValueError('A not gate can only have one input.')
        super().set_inputs(inputs)

    def calculate(self):
        self._output.state = State.high if self._inputs[0] == State.low else State.low
        return self._output.state


class NorGate(MinTwoInputComponentMixin, OneOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [OrGate(name=name), NotGate(name=name)]
        self._output = self._components[1].output_node
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        or_gate = self._components[0]
        not_gate = self._components[1]
        or_gate.set_inputs(inputs)
        not_gate.set_inputs([or_gate.output_node])


class NandGate(MinTwoInputComponentMixin, OneOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [AndGate(name=name), NotGate(name=name)]
        self._output = self._components[1].output_node
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        and_gate = self._components[0]
        not_gate = self._components[1]
        and_gate.set_inputs(inputs)
        not_gate.set_inputs([and_gate.output_node])


class XorGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        converted_inputs = [i.state >= State.high for i in self._inputs]
        result = Counter(converted_inputs)
        self._output.state = State.high if result.get(True) == 1 else State.low
        return self._output.state


class XnorGate(MinTwoInputComponentMixin, OneOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [XorGate(name=name), NotGate(name=name)]
        self._output = self._components[1].output_node
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        super().set_inputs(inputs)
        xor_gate = self._components[0]
        not_gate = self._components[1]
        xor_gate.set_inputs(inputs)
        not_gate.set_inputs([xor_gate.output_node])


class SRNorLatch(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [NorGate(name=name), NorGate(name=name)]
        self._outputs = NodeList([i.output_node for i in self._components])
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(self.name, expected_names=['Set', 'Reset'], min_length=2, max_length=2)

        super().set_inputs(inputs)
        nor_gate1 = self._components[0]
        nor_gate2 = self._components[1]
        nor_gate1.set_inputs([inputs.get_node_by_name('Reset'), nor_gate2.output_node])
        nor_gate2.set_inputs([inputs.get_node_by_name('Set'), nor_gate1.output_node])
        nor_gate1.output_node.name = f'Q'
        nor_gate2.output_node.name = f'QBar'
        self._outputs = NodeList([nor_gate1.output_node, nor_gate2.output_node])

    def calculate(self):
        self._components[0].calculate()
        self._components[1].calculate()
        self._components[0].calculate()
        return self.output_nodes

    def __str__(self):
        return f'({self._inputs["Reset"]},{self._inputs["Set"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


class SRNandLatch(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [NandGate(name=name), NandGate(name=name)]
        self._outputs = NodeList([i.output_node for i in self._components])
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(self.name, expected_names=['Set', 'Reset'], min_length=2, max_length=2)

        super().set_inputs(inputs)
        gate1 = self._components[0]
        gate2 = self._components[1]
        gate1.set_inputs([inputs.get_node_by_name('Set'), gate2.output_node])
        gate2.set_inputs([inputs.get_node_by_name('Reset'), gate1.output_node])
        gate1.output_node.name = f'Q'
        gate2.output_node.name = f'QBar'
        self._outputs = NodeList([gate1.output_node, gate2.output_node])

    def calculate(self):
        self._components[0].calculate()
        self._components[1].calculate()
        self._components[0].calculate()
        return self.output_nodes

    def __str__(self):
        return f'({self._inputs["Reset"]},{self._inputs["Set"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


class DTypeFlipFlop(MultipleOutputComponent):
    def __init__(self, inputs: Union[NodeList, list] = None, name: str = None):
        self._components = [NotGate(name=f'{name}_not'), NandGate(name=f'{name}_nand1'), NandGate(name=f'{name}_nand2'),
                            SRNandLatch(name=f'{name}_srnand')]
        self._outputs = self._components[3].output_nodes
        super().__init__(inputs, name)

    def set_inputs(self, inputs: Union[NodeList, list]):
        if isinstance(inputs, list):
            inputs = NodeList(inputs)
        inputs.validate(self.name, expected_names=['D', 'Clk'], min_length=2, max_length=2)
        super().set_inputs(inputs)
        not_gate = self._components[0]
        not_gate.set_inputs([inputs['D']])
        nand_set = self._components[1]
        nand_set.set_inputs([inputs['D'], inputs['Clk']])
        nand_set.output_node.name = 'Set'
        nand_reset = self._components[2]
        nand_reset.set_inputs([not_gate.output_node, inputs['Clk']])
        nand_reset.output_node.name = 'Reset'
        srnand = self._components[3]
        srnand.set_inputs([nand_set.output_node, nand_reset.output_node])
        self._outputs = NodeList([srnand.output_nodes['Q'], srnand.output_nodes['QBar']])

    def calculate(self):
        self._components[0].calculate()
        self._components[1].calculate()
        self._components[2].calculate()
        self._components[3].calculate()
        return self.output_nodes

    def __str__(self):
        return f'({self._inputs["D"]},{self._inputs["Clk"]} ) -> ({self._outputs["Q"]}, {self._outputs["QBar"]})'


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


if __name__ == '__main__':
    main()
