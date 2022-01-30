import lch

def main():
    teams = ['8f74e6', '8f0bbc']
    ais = [None, '6edfda']
    size_x, size_y = 20, 12
    lch.UI(teams, ais, lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y))).game_loop()

    return

if __name__ == '__main__':
    main()
