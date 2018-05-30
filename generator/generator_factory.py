"""
Provide the generator inteface and the factory
"""
import abc


class Generator(abc.ABC):
    """
    Generator interface
    """

    @abc.abstractmethod
    def generate_tile(self, tms_x, tms_y, tms_z, arguments):
        """
        Generate tile for the given x, y, z
        """
        pass

    @abc.abstractmethod
    def product_type(self):
        """
        Return product type string
        """
        pass

    @abc.abstractmethod
    def get_error_file(self):
        """
        Return product type string
        """
        pass

    @abc.abstractmethod
    def get_data_not_yet_ready_file(self):
        """
        Return product type string
        """
        pass


class GeneratorFactory:
    """
    Generator Factory is a singleton, use get_instance function
    Return the registered generator for the given type
    """

    instance = None

    def __init__(self):
        """
        init
        """
        self.generator_map = {}

    def register_generator(self, generator):
        """
        register a generator in the generator factory
        """
        product_type = generator().product_type()
        self.generator_map[product_type] = generator

    def build_generator(self, product_type):
        """
        return the generator for the given type
        """
        return self.generator_map[product_type]()

    @staticmethod
    def get_instance():
        """
        return the instance of the factory
        """
        if GeneratorFactory.instance is None:
            GeneratorFactory.instance = GeneratorFactory()
        return GeneratorFactory.instance
