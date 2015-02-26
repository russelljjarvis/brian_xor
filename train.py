import brian as br
import numpy as np
import math as ma
import pudb
import snn

def DesiredOut(label, bench):
    return_val = None

    if bench == 'xor':
        if label == 1:
            return_val = 0*br.ms
        else:
            return_val = 6*br.ms

    return return_val

def WeightChange(s):
    A = 10**-1
    tau = 2.0*br.ms
    return A*ma.exp(-s / tau)

def L(t):
    tau = 5.0*br.ms
    if t > 0:
        return ma.exp(float(-t / tau))
    else:
        return 0

def P_Index(S_l, S_d):
    return_val = 0

    if type(S_l) != list:
        pudb.set_trace()
    elif type(S_l) == list:
        if len(S_l) < 1:
            pudb.set_trace()
        elif type(S_l[0]) == list:
            if len(S_l[0]) < 1:
                pudb.set_trace()
    return_val += abs(L(S_d) - L(S_l[0][0]*br.second))

    return return_val

def TestNodeRange(T, N, v0, u0, bench, number, input_neurons, \
        liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
        hidden_neurons, output_neurons, \
        Si, Sl, Sa, Sb, M, Mv, Mu, S_in, S_hidden, S_out):

    n_hidden = len(hidden_neurons) 
    old_weights = np.empty(n_hidden)

    return_val = [-1, -1]

    for i in range(n_hidden):
        old_weights[i] = Sb.w[i]
        Sb.w[i] = 0

    j = 0
    #Sb.w[0] = 0.01
    while True:

        snn.Run(T, v0, u0, bench, number, input_neurons, \
                liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
                hidden_neurons, output_neurons, \
                Si, Sl, Sa, Sb, M, Mv, Mu, S_in, S_hidden, S_out, train=True, letter=None)

        #pudb.set_trace()
        spikes_out = S_out.spiketimes[0]
        spikes_hidden = S_hidden.spiketimes[0]
        n_outspikes = len(spikes_out)
        print "n_outspikes, Sb.w[0] = ", n_outspikes, ", ", Sb.w[0]

        if n_outspikes == 1:
            if return_val[0] == -1:
                #pudb.set_trace()
                return_val[0] = spikes_out[0] - spikes_hidden[0]
            return_val[1] = spikes_out[0]
        elif n_outspikes > 1:
            #pudb.set_trace()
            break

        Sb.w[0] = Sb.w[0] + 0.0001

        #if j % 1 == 0:
        #    snn.Plot(Mv, 0)
            
        #j += 1


    for i in range(n_hidden):
        Sb.w[i] = old_weights[i]

    return return_val

def ReSuMe(desired_times, Pc, T, N, v0, u0, bench, number, input_neurons, \
        liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
        hidden_neurons, output_neurons, Si, Sl, Sa, Sb, M, Mv, Mu, S_in, S_hidden, S_out):

    img, label = snn.ReadImg(number=number, bench=bench)
    N_hidden = len(hidden_neurons)
    N_out = len(output_neurons)

    N_h = 1
    N_o = 1

    trained = False

    while trained == False:
        for i in range(N_hidden):

            #print "\t\ti = ", i
            #pudb.set_trace()
            label = snn.Run(T, v0, u0, bench, number, input_neurons, \
                        liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
                        hidden_neurons, output_neurons, \
                        Si, Sl, Sa, Sb, M, Mv, Mu, S_in, S_hidden, S_out, train=True, letter=None)

            snn.SaveConnectivity(Si, Sl, Sa, Sb, 1)
            #pudb.set_trace()

            print "Spike Times: ", S_hidden.spiketimes, " ", S_out.spiketimes
            done = snn.CheckNumSpikes(-1, T, N_h, N_o, v0, u0, bench, number, input_neurons, \
                        liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
                        hidden_neurons, output_neurons, \
                        Si, Sl, Sa, Sb, M, Mv, Mu, \
                        S_in, S_hidden, S_out, train=False, letter=None)

            if done == False:
                print "ERROR!! WRONG NUMBER OF SPIKES!! Resetting No. Spikes!!!"
                pudb.set_trace()
                """
                snn.SetNumSpikes(T, N_h, N_o, v0, u0, bench, number, input_neurons, \
                        liquid_in, liquid_hidden, liquid_out, liquid_neurons, \
                        hidden_neurons, output_neurons, \
                        Si, Sl, Sa, Sb, M, Mv, Mu, \
                        S_in, S_hidden, S_out, train=False, letter=None)
                """

            #pudb.set_trace()
            S_l = S_out.spiketimes
            S_i = S_hidden.spiketimes
            S_d = desired_times[label]

            P = P_Index(S_l, S_d)
            print "\t\t\tP = ", P
            if P < Pc:
                trained = True
                break

            #pudb.set_trace()
            sd = max(0, float(S_d) - S_i[i][0])
            sl = max(0, S_l[0][0] - S_i[i][0])
            Wd = WeightChange(sd)
            Wl = -WeightChange(sl)
            Sb.w[i] = Sb.w[i] + Wd + Wl

def SpikeSlopes(Mv, S_out, d_i=3):
    
    """
        Returns a list of values that indicate the difference in voltage 
        between each spike's starting threshold voltage and the voltage 
        d_i time steps before it

        NOTE: This assumes that the brian equation solver uses a constant time step
        throught computation.
    """

    N = len(S_out.spikes)
    dt = Mv.times[1] - Mv.times[0]
    v_diffs = []
    i_diffs = []

    for i in range(N):
        time = S_out.spikes[i]
        index_a = time / dt
        index_b = index_a - d_i 

        v_diffs.append(Mv.values[index_a] - Mv.values[index_b])
        i_diffs.append(index_a - index_b)

    return v_diffs, dt

def PickWeightIndexA(Sa, S_hidden, S_out):
    pass

def PickWeightIndicesB(Mv, Sb, S_hidden, S_out, d_i=3):

    """
        Depending on the delays of the synapses, and the spike times
        in the hidden layer and output layer, modification of only certain of the weights
        in the hidden to output synapses will have an effect on each output spike

    """

    v_diffs, i_diffs = SpikeSlopes(Mv, S_out, d_i)

    

def dWa(Sa, v_diffs, i_diffs):
    pass
