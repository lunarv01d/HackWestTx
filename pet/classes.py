class pet:
    def __init__(self, name, species, age):
        self.name = name
        self.species = species
        self.age = age
        self.height = 1
        self.hunger = 50
        self.energy = 100
        self.pods = 0 #max 5

    def get_info(self):
        return f"{self.name} is a {self.age}-year-old {self.species}."
    
    def water(self):
        self.hunger = max(self.hunger - 20, 0)
        print(f"{self.name} has been watered!")
        
    def sunlight(self):
        self.energy = min(self.energy + 20, 100)
        print(f"{self.name} has received sunlight!")
        
    def growA(self):
        self.age += 1
        print(f"{self.name} has grown older! Now {self.age} years old.")
        
    def growH(self):
        self.height += 1
        print(f"{self.name} has grown taller! Now {self.height} units tall.")
        
    def growP(self):
        self.pods += 1
        print(f"{self.name} has grown pods! Now {self.pods} pods.")
    
        