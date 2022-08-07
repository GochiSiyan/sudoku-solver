from itertools import chain
from math import prod
from copy import deepcopy

from sudoku import *

class Solver:
    def __init__(this, **kwargs):
        if kwargs.get('data'):
            this.data = kwargs['data']
        else:
            this.data = {}
            this.data['set'] = set(i for i in range(10)) #set of numbers allowed in sudoku.
            this.data['sudoku'] = this.sudoku(kwargs['sudoku']) #Initialize sudoku, clarify, and prepare data
            this.data['index'] = this.indexer() #track the index information
            this.data['maybe'] = this.maybe() #check and store the possible number on the empty square with basic strategy

            this.data['template'] = this.template() #template caching
            this.data['unique'] = {} #unique caching
            this.data['coor'] = None #coor caching
            this.data['iter'] = {} #solver flag variable
            this.data['brute'] = True #brute flag

    def maybe(this):
        maybe = {}
        index = [set() for i in range(10)]
        for i in this.data['index'][0]:
            for j in (loop := this.data['set']\
                - set(
                    this.getter(i, 0) +
                    this.getter(i, 1) +
                    this.getter(i, 2)
                )):
                index[j].add(i)
            maybe[i] = loop

        return (maybe, dict(
            zip(
                [i for i in range(1, 10)],
                index[1:]
            )
        ))
    
    def getter(this, index, type):
        """
        Helper function to get list depending on the indexing type
        """
        coor = this.coor(index)

        return [this.data['sudoku'][3][i] for i in this.data['sudoku'][type][coor[type]]]

    def coor(this, coor):
        """
        helper function to get index of sudoku given the coordinate
        """
        this.data['coor'] = [x := coor%9, y := coor//9, x//3 + y//3 * 3]
        return this.data['coor']

    def indexer(this):
        ret = [set() for i in range(10)]
        for ix,i in enumerate(this.data['sudoku'][3]):
            ret[i].add(ix)
        return ret

    def solve(this):
        while this.iterget():
            this.cycle()
            this.unique()

            if not this.iterget() and\
                this.status()['code'] == 1 and\
                this.data['brute']:
                this.brute()
        this.iterset()

    def cycle(this):
        """
        cycle through the maybe and assign if the maybe is 1
        """
        while this.iterget('cycle'):
            indexes = []
            for index,maybe in this.data['maybe'][0].items():
                if len(maybe) == 1:
                    for value in maybe:
                        indexes.append((index, value))
            this.multisign(*indexes)
            this.iterset('cycle', bool(indexes))

    def unique(this):
        """
        cycle to see if the empty has only one possible solution
        """
        while this.iterget('unique'):
            indexes = []
            for index,maybe in this.data['maybe'][0].items():
                intersection = this.intersection(index) - {index} #get all intersection of an index
                for i in range(3): #loop the 3 type and check if any unique available
                    flag = False
                    for j in (maybe - set(
                        chain(
                            *[this.data['maybe'][0][k] for k in (set(
                                this.data['sudoku'][i][
                                    this.data['coor'][i]
                                ]
                            ) & intersection)]
                        )
                    )):
                        indexes.append((index, j))
                        flag = True
                        break
                    if flag: break
            this.multisign(*indexes)
            this.iterset('unique', bool(indexes))

    def iterset(this, key = '', value = True):
        if value:
            for i in this.data['iter']:
                this.data['iter'][i] = True
        if key: this.data['iter'][key] = value

    def iterget(this, key = ''):
        return this.data['iter'].get(key, True)\
            if key\
            else prod(this.data['iter'].values())

    def intersection(this, index):
        """
        Helper function to get all the intersection of empty square
        """
        coor = this.coor(index)
        return set(
            chain(*[this.data['sudoku'][i][coor[i]] for i in range(3)])
        ) & this.data['index'][0]

    def assign(this, index, value):
        """
        Handles the sudoku number assignment and update internal information
        """
        this.data['sudoku'][3][index] = value #update sudoku
        this.data['index'][value].add(index) #update index information
        this.data['index'][0].remove(index)

        #update maybe information
        # remove maybe 0 key
        # update maybe 1 index
        for i in this.data['maybe'][0][index]:
            this.data['maybe'][1][i].remove(index)
        del this.data['maybe'][0][index]

        this.unmaybe(
            *[(i, value) for i in this.intersection(index) & this.data['maybe'][1][value]]
        )

    def unmaybe(this, *args):
        for i in args:
            this.data['maybe'][0][i[0]].remove(i[1])
            this.data['maybe'][1][i[1]].remove(i[0])

    def brute(this):
        """
        Also known as bifurcation
        The last resort if basic strategy no longer helps.
        It will intelligently test wether the guess is valid or not and continue with the simple strat from there.
        """
        for index,maybe in this.data['maybe'][0].items():
            # if len(maybe) != 2: continue #only do the square with 2 possibilities

            for i in maybe:
                tester = this.__class__(data = {**deepcopy(this.data), 'brute':False})
                tester.assign(index, i)
                tester.iterset()
                tester.solve()

                if (status := tester.status()['code']) == 2:
                    this.unmaybe((index, i))
                    this.iterset() #repeat the solve cycle
                    return
                if status == 0:
                    this.assign(index, i)
                    this.iterset() #repeat the solve cycle
                    return

    def multisign(this, *args):
        """
        Help to quickly assign multiple value
        """
        for i in args:
            this.assign(*i)

    def sudoku(this, sudoku):
        #prepare raw data into a more digestable form.
        ret = [
            [
                [
                    i + j*9 for j in range(9)
                ] for i in range(9)
            ], #vertical index
            [
                [
                    i*9 + j for j in range(9)
                ] for i in range(9)
            ], #horizontal index
            [[] for i in range(9)],
            list(chain(*sudoku)) #the core data number
        ]
        
        #transpose sudoku to square index 
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    for l in range(3):
                        ret[2][i*3 + j].append(9*(3*i+k) + 3*j+l)

        return ret
    
    def status(this):
        for i in this.data['maybe'][0].values():
            if not i:
                return {
                    'code':2,
                    'status':'invalid'
                    }

        if set(chain(*this.data['maybe'][1].values())):
            return {
                'code':1,
                'status':'unsolved'
                }
        else:
            return {
                'code':0,
                'status':'solved'
                }

    def error(this, **kwargs):
        [print("%s %s" % (i, j)) for i,j in kwargs.items()]
        raise Exception("Not Sudoku")

    def template(this):
        return """╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╟───┼───┼───╫───┼───┼───╫───┼───┼───╢
║ %s │ %s │ %s ║ %s │ %s │ %s ║ %s │ %s │ %s ║
╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝"""

    def p_sudoku(this):
        print(this.data['template'] % tuple(i for i in this.data['sudoku'][3]))

    def p_pos(this, number):
        ret = list(this.data['sudoku'][3])

        for i in this.data['maybe'][1][number]:
            ret[i] = 'X'

        print(this.data['template'] % tuple(ret))

solve = Solver(sudoku = hard2)
solve.solve()
print(solve.status())
solve.p_sudoku()