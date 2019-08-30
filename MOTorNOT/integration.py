import numpy as np
import pandas as pd
import attr 
from scipy.integrate import solve_ivp
from scipy.constants import physical_constants
amu = physical_constants['atomic mass constant'][0]
from MOTorNOT import load_parameters
atom = load_parameters()['atom']

def generate_initial_conditions(x0, v0, theta=0, phi=0):
    ''' Generates atomic positions and velocities along the z
        axis, then rotates to the spherical coordinates theta and
        phi.
    '''
    theta *= np.pi/180
    phi *= np.pi/180

    lenx = 0
    if hasattr(x0, '__len__'):
        lenx = len(x0)
    lenv = 0
    if hasattr(v0, '__len__'):
        lenv = len(v0)

    length = np.maximum(lenx, lenv)

    X = np.zeros((length, 3))
    X[:, 2] = x0

    V = np.zeros((length, 3))
    V[:, 2] = v0

    Rx = np.array([[1, 0, 0], [0, np.cos(theta), -np.sin(theta)], [0, np.sin(theta), np.cos(theta)]])
    Rz = np.array([[np.cos(phi), -np.sin(phi), 0], [np.sin(phi), np.cos(phi), 0], [0, 0, 1]])
    X = X.dot(Rx).dot(Rz)
    V = V.dot(Rx).dot(Rz)
    return X, V

from MOTorNOT.analysis import *

@attr.s
class Solver:
    acceleration = attr.ib()
    X0 = attr.ib(converter=np.atleast_2d)
    V0 = attr.ib(converter=np.atleast_2d)

    def run(self, duration, dt=None):
        self.y, self.X, self.V, self.t = solve(self.acceleration,
                                       self.X0,
                                       self.V0,
                                       duration, dt=dt)
        return self

    def plot_trajectory(self, plane='xy'):
        plot_trajectories(self.acceleration, self.X, self.t, plane=plane)

    def plot_phase_space(self, axis='x'):
        plot_phase_space_trajectories(self.acceleration, self.X, self.V, axis=axis)

def solve(acceleration, X0, V0, duration, dt=None):
    ''' Integrates the equations of motion given by the specified force,
        starting from given initial conditions.
    '''

    def dydt(t, y):
        ''' Args:
                y (array-like): Array of length N where the first N/2 values correspond
                                to position and the last N/2 to velocity.
            Returns:
                '''
        N = int(len(y)/6)
        ''' Reconstruct arrays in (N,3) shape from flattened arrays '''
        X = y[0:3*N].reshape(N,3)
        V = y[3*N::].reshape(N,3)

        a = acceleration(X, V)

        return np.append(V.flatten(), a.flatten())

    y0 = np.append(np.array(X0).flatten(), np.array(V0).flatten())
    if dt is not None:
        t_eval = np.arange(0, duration, dt)
        r = solve_ivp(dydt, (0, duration), y0, t_eval=t_eval, vectorized=True)
    else:
        r = solve_ivp(dydt, (0, duration), y0, vectorized=True)

    t = r.t
    y = r.y
    N = int(len(y)/6)

    X = y[0:3*N, :].T
    V = y[3*N:6*N, :].T
    X = X.reshape(-1, N, 3)
    V = V.reshape(-1, N, 3)
    return y, X, V, t
