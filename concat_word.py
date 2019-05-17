import argparse
import os
import sys

idioms_txt = "idioms.txt"

def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("txt_fname")
    args = parser.parse_args()

    if not os.path.exists(args.txt_fname):
        print('File does not exist: {0}'.format(args.txt_fname))
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    with open(idioms_txt) as f:
        idioms = f.readlines()

    with open(args.txt_fname) as f:
        for line in f.readlines():
            for idiom in idioms:
                idiom = idiom.strip()
                line = line.replace(idiom, idiom.replace(" ", "_"))
                line = line.replace(idiom.capitalize(), idiom.replace(" ", "_").capitalize())
            print(line, end = "")

if __name__ == '__main__':
    main()
