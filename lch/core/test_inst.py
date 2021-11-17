from lch import Weapon, Model, Team, NoRangedWeapon

TestRifle1 = Weapon('Test R1', 18, 1, 0, 2, 4)
TestHeavy1 = Weapon('Test RH', 24, 3, 1, 3, 5, "heavy")
TestRifle2 = Weapon('Test R2', 12, 2, 0, 3, 4)
TestAssault2 = Weapon('Test RA', 12, 3, 1, 3, 4, "assault")

Knife = Weapon('Knife', range=1, min_damage=2, max_damage=3)
Sword = Weapon('Sword', range=1, attacks=2, min_damage=3, max_damage=4)
Axe = Weapon('Axe', range=1, attacks=3, min_damage=4, max_damage=5)

test_1_kwargs={'movement': 6, 'ranged_skill': 55, 'ranged_consistency': 15,'armor':2,
        'melee_skill': 45, 'melee_consistency': 15, 'dodge': 60, 'health': 6}
TestModel1 = Model(name='Test1', melee_weapon=Knife, ranged_weapon=TestRifle1, **test_1_kwargs)
TestModel1a = Model(name='Test1a', melee_weapon=Knife, ranged_weapon=TestHeavy1, **test_1_kwargs)
TestModel1b = Model(name='Test1b', melee_weapon=Sword, ranged_weapon=NoRangedWeapon, **test_1_kwargs)

test_2_kwargs={'movement': 6, 'ranged_skill': 45, 'ranged_consistency': 25,'armor': 1,
        'melee_skill': 60, 'melee_consistency': 20, 'dodge': 50, 'health': 7}
TestModel2 = Model(name='Test1', melee_weapon=Sword, ranged_weapon=TestRifle2, **test_2_kwargs)
TestModel2a = Model(name="Test2a", melee_weapon=Sword, ranged_weapon=TestAssault2, **test_2_kwargs)
TestModel2b = Model(name='Test2b', melee_weapon=Axe, ranged_weapon=NoRangedWeapon, **test_2_kwargs)

TestTeam1 = Team([TestModel1] + [TestModel1a] + [TestModel1b])
TestTeam2 = Team([TestModel2] + [TestModel2a] + [TestModel2b])
