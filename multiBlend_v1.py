
import numpy as np
from numpy import array
from numpy import hstack

from ortools.linear_solver import pywraplp


def main():
    s = pywraplp.Solver('blender', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)

    # bsQuality[blendstock][quality]
    bsQuality = [['Alk1', 95, 87, 33],
                 ['Ref1', 101, 93, 33],
                 ['LSR', 75, 65, 33],
                 ['88R', 88, 76, 33],
                 ['90R', 90, 81, 33],
                 ['100R', 100, 91, 33]]

    # cost[blendstock][period +1]
    cost = [['alk1', 100, 99, 98, 97],
            ['Ref1', 110, 109, 108, 107],
            ['LSR', 70, 69, 68, 67],
            ['88R', 90, 89, 88, 87],
            ['90R', 93, 92, 91, 90],
            ['100R', 127, 100, 110, 135]]

    # prQualityMin[product][quality +1]
    prQualityMin = [['91R', 91, 81, 0],
                    ['95R', 95, 85, 0],
                    ['98R', 98, 86, 0]]

    prQualityMax = [['91R', 99, 99, 99],
                    ['95R', 99, 99, 99],
                    ['98R', 99, 99, 99]]

    pr = len(prQualityMin[0]) - 1  # number of products
    p = len(cost[0]) - 1  # number of periods
    b = len(bsQuality)  # number of blendstocks
    sp = len(prQualityMin[0]) - 1  # number of specs
    period = range(p)
    blendstock = range(b)
    product = range(pr)
    demand = 5000

    spec = range(sp)

    SL = [0, 1000]  # min and max holding qty

    print(f'There are {p} periods.\nThere are {b} blendstocks.')

    # create array variables
    # buy = qty of blendstock bought each period
    # buy[blendstock][period]
    buy = [[s.NumVar(0, s.infinity(), '') for _ in period] for _ in blendstock]

    # blend = qty of blendstock consumed (blended) per period
    # blend[product][blendstock][period]
    blend = [[[s.NumVar(0, s.infinity(), '') for i in period]
              for j in blendstock] for k in product]

    # hold = qty of blendstock held in tankage from one period to the next
    # first period will use opening Inventory
    # hold[blendstock][period]
    hold = [[s.NumVar(0, s.infinity(), '') for i in period] for j in blendstock]

    # produced = qty of each product blended, must equal demand.
    # produced[product][period]
    produced = [[s.NumVar(0, s.infinity(), '') for i in period] for k in product]

    # purchaseCose = total cost of blendstock per period.
    # TODO, create a cost per blendstock for reporting
    # purchaseCost[period]
    purchaseCost = [s.NumVar(0, s.infinity(), '') for i in period]
    # purchaseCost = [[s.NumVar(0, s.infinity(), '') for i in period] for k in product]

    # quality[spec][product][period]
    quality = [[[s.NumVar(0, s.infinity(), '') for _ in period]
                for _ in product] for _ in spec]

    # quality = qty * quality of blendstock qualities.
    # quality[quality][product][period]
    # quality = [[[s.NumVar(0, s.infinity(), '') for i in period]
    #             for k in product] for l in spec]

    # set opening inventory
    for j in blendstock:
        s.Add(hold[j][0] == 1)  # todo, set opening inventory

    # set produced to equal sum of blendstock blended into each product
    for k in product:
        for i in period:
            s.Add(produced[k][i] == sum(blend[k][j][i] for j in blendstock))
            s.Add(produced[k][i] >= demand)

    # for each period, ensure blendstock inventory is between limits.
    # This uses SL.  TODO, make this by grade
    for i in period:
        if i < period[-1]:
            for j in blendstock:
                heldUpdate = hold[j][i] + buy[j][i] - sum(blend[k][j][i] for k in product)
                s.Add(heldUpdate == hold[j][i + 1])
        s.Add(sum(hold[j][i] for j in blendstock) >= SL[0])
        s.Add(sum(hold[j][i] for j in blendstock) <= SL[1])

    for i in period:
        for k in product:
            for l in spec:
                s.Add(quality[l][k][i] == sum(blend[k][j][i]
                                              * bsQuality[j][l + 1] for j in blendstock))

                s.Add(quality[l][k][i] >= prQualityMin[k][l + 1] * produced[k][i])
                s.Add(quality[l][k][i] <= prQualityMax[k][l + 1] * produced[k][i])

    for i in period:
        s.Add(purchaseCost[i] == sum(buy[j][i] * cost[j][i + 1] for j in blendstock))

    totalCost = s.Sum(purchaseCost[i] for i in period)

    s.Minimize(totalCost)
    status = s.Solve()
    if status == s.OPTIMAL:
        print('hooray')
        print('Objective = ', s.Objective().Value())
        for i in period:
            print('--------------------')
            print('Period ', i)
            for k in product:
                print('Material blended :',
                      prQualityMin[k][0], ' = ', produced[k][i].solution_value())
                for j in blendstock:
                    print(bsQuality[j][0], ' = ', blend[k][j][i].solution_value())
                print('--------------------')


if __name__ == '__main__':
    main()
