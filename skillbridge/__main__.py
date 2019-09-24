from os.path import abspath, dirname, join


if __name__ == '__main__':
    folder = dirname(abspath(__file__))
    skill_source = join(folder, 'server', 'python_server.il')
    print(skill_source)
