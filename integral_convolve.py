import numpy as np
import matplotlib.pyplot as plt
import itertools
import matplotlib

from numpy.linalg import eig

def torus_point(theta, phi, R, r):
    """ Takes R, r, theta and phi. Returns a 3D vector of Euclidean coordinates."""
    x = np.zeros(3)
    x[0] = (R+r*np.cos(theta))*np.cos(phi)
    x[1] = (R+r*np.cos(theta))*np.sin(phi)
    x[2] = r*np.sin(theta)
    return x

def log_kernel(point1, point2):
    return np.log(np.linalg.norm(point2-point1))

def exp_kernel(point1, point2):
    return np.exp(-np.linalg.norm(point2-point1))

def square_distance_kernel(point1, point2):
    return np.linalg.norm(point2-point1)**2

def full_matrix(N, kernel_func, lamb, R, r, self_interact = True):
    """ Construct the full matrix (I+lambda*K) (dim N^2 x N^2) in the equation: g = (I+K)f"""
    result = np.zeros([N**2,N**2])
    for i in range(N**2):
        for j in range(N**2):
            result[i,j]= lamb*matrix_entry(i,j,N, kernel_func, R, r, self_interact)
            if i==j:
                result[i,j] = result[i,j] + 1
    return result

def matrix_entry(i, j, N, kernel_func, R, r, self_interact = True):
    """ Return the (i,j) entry of the matrix K(‖x(θ,φ)−x′(θ′,φ′)‖)r(R+rcosθ′)*(2pi/N)^2,
        where K is the kernel generated by kernel_func, which takes two 3d vectors as input. e.g. kernel(point2, point1) = log(distance)
        i, j =  0,1,..., N^2-1
        If self_interact is false, the K(x,x') is undefined -> set to 0 
    """
    theta1 = i//N*(2*np.pi/N); phi1 = i%N*(2*np.pi/N); point1 = torus_point(theta1, phi1, R=R, r=r)
    theta2 = j//N*(2*np.pi/N); phi2 = j%N*(2*np.pi/N); point2 = torus_point(theta2, phi2, R=R, r=r)

    if i==j and (not self_interact):
        entry = 0
    else:
        entry = (2*np.pi/N)**2*kernel_func(point1, point2)*r*(R+r*np.cos(theta2))
    return entry

def get_cyclic_reps(N):
    """ Return regular representations of cyclic group, sorted in ascending order of group elements: i.e. 0,1,..N-1"""
    A = []
    for i in range(N-1,-1,-1):
        A.append([1 if j == i else 0 for j in range(N)])
    perms = []    
    for i in range(N):
        perms.append(np.array([A[i-j] for j in range(N)]))
    I = perms.pop(-1)
    return [I] + perms

def get_cyclic_product_reps(N):
    """ Return INVERSE regular representations (permutation matrices of size N^2 x N^2) of the direct product of a cyclic group to itself, 
            sorted in ascending order of group elements: i.e. (0,0),(0,1),,..(N-1,N-1)"""
    group1 = get_cyclic_reps(N)
    group2 = get_cyclic_reps(N)
    reps = []
    for mat1 in group1:
        for mat2 in group2:
            reps.append(np.kron(mat1, mat2))
    sorted_reps = sorted(reps, key= lambda mat: np.argmax(mat[:,0]))
    return [rep.T for rep in sorted_reps]

def get_filter(N, kernel_func, lamb, R, r, self_interact = True):
    m = [lamb*matrix_entry(0, 0, N, kernel_func, R, r, self_interact)+1]
    for j in range(1,N**2):
            m.append(lamb*matrix_entry(0,j,N, kernel_func, R, r, self_interact))
    return np.array(m)

def f(theta, phi):
    """ Function on torus to be solved."""
    # return np.cos(phi)
    # return np.cos(phi) * np.cos(theta)
    return (theta-np.pi)**2 + (phi-np.pi)**2

def g(theta, phi, lamb, r):
    """ LHS of integral equation. Note: R=1 fixed"""
    # return np.cos(phi) - lamb*2*(np.pi**2)*r*np.cos(phi)*(2+r**3*np.cos(theta)+r**2+2*r*np.cos(theta))
    # return np.cos(phi) * np.cos(theta) - lamb*(2*np.pi*r)**2*np.cos(phi)*(1+r*np.cos(theta))
    return (theta-np.pi)**2 + (phi-np.pi)**2 + lamb*2/3*np.pi**2*r*(
                        8*np.pi**2+48*r+(3+12*np.pi**2)*r**2+24*r**3 
                        + (8*np.pi**2*r+24*r**2)*np.cos(theta)+
                        + (-24-12*r**2)*np.cos(phi)
                        + (-12*r**3-24*r)*np.cos(theta)*np.cos(phi))

def discretized_f(N):
    vec = []
    for i in range(N):
        for j in range(N):
            vec.append(f(i*2*np.pi/N, j*2*np.pi/N))
    return np.array(vec)

def discretized_g(lamb, r, N):
    vec = []
    for i in range(N):
        for j in range(N):
            vec.append(g(i*2*np.pi/N, j*2*np.pi/N, lamb, r))
    return np.array(vec)

# N1=50
# X,Y = np.meshgrid(7/N1*np.array(list(range(-N1,N1))), 10/N1*np.array(list(range(-N1,N1))))
# Z = g(X, Y, -0.1, 0.2)
# plt.figure()
# ax = plt.axes(projection='3d')
# ax.plot_wireframe(X, Y, Z, color='blue', alpha=0.8)
# plt.show()

if __name__=="__main__":
    R = 1  ## do not change this
    lamb = -1  ## do not change this
    
    kernel = square_distance_kernel
    fig = plt.figure()
    err = []
    for index, N in enumerate([4,6,8,10,12,14,16,32]):
        r = 0.05  ## change this
        # N = 16  ## discretized points
        
        g_vec = discretized_g(lamb, r, N)

        reps = get_cyclic_product_reps(N)
        filter = get_filter(N, kernel, lamb, R, r, self_interact=True)
        approx = np.zeros([N**2, N**2])
        for i in range(N**2):
            approx = approx + filter[i]*reps[i]

        # A = full_matrix(N, kernel, lamb, R, r, self_interact=True)
        # print(np.linalg.norm(approx-A, ord='fro')/(N**4))

        sol = np.reshape(np.linalg.inv(approx)@np.array([g_vec]).T,-1)

        # eigs, _ = np.linalg.eig(approx)
        # print(np.min(np.abs(eigs)))

        f_vec = discretized_f(N)
        err.append(np.mean(np.abs(sol-f_vec)))

    plt.plot([4,8,12,16,20,24,28,32], err, '-o')
    plt.yscale("log")
    plt.xscale("log")
    plt.xlabel("n")
    plt.ylabel("Error")
    plt.show()


        ##### 3D plots  
    #     thetas = np.repeat(2*np.pi/N*np.array(list(range(N))),N)
    #     phis = np.tile(2*np.pi/N*np.array(list(range(N))),N)
        

    #     ax = fig.add_subplot(2, 2, index+1, projection='3d')
    #     ax.grid(False)
    #     ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    #     ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
    #     ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

    #     ax.scatter(thetas, phis, sol, c=sol, label = "approx", cmap='autumn',  marker= ".", alpha = 0.99, s=6)

    #     N1 = 1000
    #     X,Y = np.meshgrid(2*np.pi/N1*np.array(list(range(N1))), 2*np.pi/N1*np.array(list(range(N1))))
    #     Z = f(X, Y)
    #     ax.plot_surface(X, Y, Z, color='steelblue', alpha=0.5, linewidth=0)  #, cmap=matplotlib.cm.Blues
    #     res = 1000
    #     x = np.linspace(0, (N1-1)/N1*2*np.pi, res)
    #     ax.plot(x, 0*np.ones(res), f(x, 0), color='steelblue', lw=1, zorder=5)
    #     ax.plot(x, (N1-1)/N1*2*np.pi*np.ones(res), f(x, (N1-1)/N1*2*np.pi), color='steelblue', lw=1, zorder=5)
    #     ax.plot(0*np.ones(res), x, f(0, x), color='steelblue', lw=1, zorder=5)
    #     ax.plot((N1-1)/N1*2*np.pi*np.ones(res), x, f((N1-1)/N1*2*np.pi, x), color='steelblue', lw=1, zorder=5)

    #     ax.set_title(f'n = {N}')
    #     ax.set_xlabel(r'$\theta$')
    #     ax.set_ylabel(r"$\varphi$")
    #     ax.set_zlabel(r"$f(\theta, \varphi$)")
    #     plt.xticks([0, np.pi, 2*np.pi ], ['0', 'π','2π'])
    #     plt.yticks([0, np.pi, 2*np.pi ], ['0', 'π','2π'])
    #     plt.locator_params(axis='z', nbins=4)
    #     ax.xaxis.set_rotate_label(False)
    #     ax.yaxis.set_rotate_label(False)
    #     # ax.zaxis.set_rotate_label(False)
    #     plt.subplots_adjust(wspace=0)

    # plt.show()



    #### 2D plots
    # angles = 2*np.pi/N*np.array(list(range(N)))
    # plt.figure()
    # plt.plot(angles, sol[:-1:N], "-o", label = 'approx')

    # N=1000
    # plt.plot(2*np.pi/N*np.array(list(range(N))), discretized_f(N)[:-1:N], label = "actual")

    # plt.legend()
    # plt.xlabel(r"$\varphi$")
    # plt.ylabel(r"$f(\theta, \varphi$)")
    # plt.show()






























# class QRAM_tree:
#     """ Data structure in Quantum recommendation system algorithm"""
#     def __init__(self, v):
#         """ v vector of 2**n non negative entries"""
#         self.v = v
#         self.N = self.v.shape[0]
#         if self.N==2:
#             self.left_value = v[0]**2
#             self.right_value = v[1]**2
#             self.value = self.left_value + self.right_value
#             self.left_child = None
#             self.righ_child = None
#             self.is_leaf = True
#         else:

#             self.is_leaf = False
#             self.left_child = QRAM_tree(v[:self.N//2])
#             self.right_child = QRAM_tree(v[self.N//2:])
#             self.left_value = self.left_child.get_value()
#             self.right_value = self.right_child.get_value()
#             self.value = self.left_value + self.right_value

#     def get_left_value(self):
#         return self.left_value
#     def get_right_value(self):
#         return self.right_value
#     def get_value(self):
#         return self.value
#     def get_left_child(self):
#         return self.left_child
#     def get_right_child(self):
#         return self.right_child
 
# v= np.array([0.4, 0.4, 0, 0.2, 0, 0, 0, 0.8])
# data = QRAM_tree(v)
# print(data.get_left_child().is_leaf)

# def get_oracle_Am(m):
#     """ m must be a 2**n vector of non-negative entries. Return: Operator Am that prepares sqrt(m_i)/|m|_1 |i>
#     """
#     tree = QRAM_tree(np.sqrt(m))
#     qubit = 0









        









