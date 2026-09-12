class pet:
    def __init__(self, name, species, age):
        self.name = name
        self.species = species
        self.age = age

    def get_info(self):
        return f"{self.name} is a {self.age}-year-old {self.species}."
    
    def feed(self):
        self.hunger = max(self.hunger - 20, 0)
        print(f"self.name")