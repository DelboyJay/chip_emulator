import enum
from collections import Counter
from typing import List


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
    _id_counter = 1

    def __init__(self, state: State = State.low, name: str = None):
        self.state = state
        Node._id_counter += 1
        if name:
            self.name = name
        else:
            self.name = f'Node{Node._id_counter}'

    def __str__(self):
        return f'{self.name}: {str(self.state)}'


class ComponentMixin:
    _inputs = NotImplemented
    _output = None
    _name = None

    def __init__(self, inputs: List[Node] = None, name: str = None):
        if inputs:
            self.set_inputs(inputs)
        if name is None:
            name = f'{self.__class__.__name__}'
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f'{self.name}: ({", ".join([str(i) for i in self._inputs])}) -> ({str(self._output)})'

    def set_inputs(self, inputs: List[Node]):
        self._inputs = inputs


class MinTwoInputComponentMixin:
    def set_inputs(self, inputs: List[Node]):
        if inputs and len(inputs) < 2:
            raise ValueError(f'{self.__class__.__name__} must have two or more inputs.')
        super().set_inputs(inputs)


class OneOutputComponent(ComponentMixin):
    def __init__(self, inputs: List[Node] = None, name: str = None):
        super().__init__(inputs, name)
        out_name = f'{name}_out' if name else None
        if not self._output:
            self._output = Node(name=out_name)

    def calculate(self):
        raise NotImplementedError

    @property
    def output_node(self):
        return self._output


class MultipleOutputComponent(ComponentMixin):
    _outputs = NotImplemented
    _components = NotImplemented

    def calculate(self):
        for c in self._components:
            c.calculate()
        return self.output_nodes

    @property
    def output_nodes(self):
        return self._outputs


class OrGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        self._output.state = State.high if any(i.state >= State.high for i in self._inputs) else State.low
        return self._output.state


class AndGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        self._output.state = State.high if all(i.state >= State.high for i in self._inputs) else State.low
        return self._output.state


class NotGate(OneOutputComponent):
    def set_inputs(self, inputs: List[Node]):
        if len(inputs) != 1:
            raise ValueError('A not gate can only have one input.')
        super().set_inputs(inputs)

    def calculate(self):
        self._output.state = State.high if self._inputs[0] == State.low else State.low
        return self._output.state


class NorGate(MinTwoInputComponentMixin, OneOutputComponent):
    def __init__(self, inputs: List[Node] = None, name: str = None):
        self._components = [OrGate(name=name), NotGate(name=name)]
        self._output = self._components[1].output_node
        super().__init__(inputs, name)

    def set_inputs(self, inputs: List[Node]):
        super().set_inputs(inputs)
        or_gate = self._components[0]
        not_gate = self._components[1]
        or_gate.set_inputs(inputs)
        not_gate.set_inputs([or_gate.output_node])

    def calculate(self):
        for c in self._components:
            c.calculate()
        return self.output_node.state


class NandGate(AndGate):
    def calculate(self):
        super().calculate()
        node = NotGate([self._output])
        self._output = node.output_node
        return node.calculate()


class XorGate(MinTwoInputComponentMixin, OneOutputComponent):
    def calculate(self):
        converted_inputs = [i.state >= State.high for i in self._inputs]
        result = Counter(converted_inputs)
        self._output.state = State.high if result.get(True) == 1 else State.low
        return self._output.state


class XnorGate(XorGate):
    def calculate(self):
        super().calculate()
        node = NotGate([self._output])
        self._output = node.output_node
        return node.calculate()


class SRNorLatch(MultipleOutputComponent):
    def __init__(self, inputs: List[Node] = None, name: str = None):
        self._components = [NorGate(name=name), NorGate(name=name)]
        self.set_inputs(inputs)
        super().__init__(inputs, name)

    def set_inputs(self, inputs: List[Node]):
        if inputs and len(inputs) != 2:
            raise ValueError(f'{self.name} must have two inputs.')

        super().set_inputs(inputs)
        nor_gate1 = self._components[0]
        nor_gate2 = self._components[1]
        nor_gate1.set_inputs(inputs + [nor_gate2.output_node])
        nor_gate2.set_inputs(inputs + [nor_gate1.output_node])
        self._outputs = [nor_gate1.output_node, nor_gate2.output_node]


def main():
    a = NorGate(name='NOR1')
    b = NorGate(name='NOR2')
    a.set_inputs([Node(State.high, name='IN1'), b.output_node])
    b.set_inputs([Node(State.high, name='IN2'), a.output_node])
    print(a.calculate())
    print(a, b)
    print(b.calculate())
    print(a, b)

    print(a.calculate())
    print(a, b)
    print(b.calculate())
    print(a, b)


if __name__ == '__main__':
    main()
