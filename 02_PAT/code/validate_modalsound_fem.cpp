// External driver for unchanged educational ModalSound tetrahedral FEM.
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include "deformable/stvk.h"
#include "deformable/fem.hpp"

static void output(const PardisoMatrix<double>& a, const std::string& path) {
    std::ofstream f(path);
    f << std::setprecision(17) << a.num_rows() << ' ' << a.num_nonzeros() << '\n';
    for (int row = 0; row < a.num_rows(); ++row)
        for (int j = a.row_indices()[row]-1; j < a.row_indices()[row+1]-1; ++j)
            f << row << ' ' << a.col_indices()[j]-1 << ' ' << a.data()[j] << '\n';
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::ifstream input(argv[1]);
    int nv, nt, fixed;
    double young, poisson;
    if (!(input >> nv >> nt >> fixed >> young >> poisson)) return 3;
    FixedVtxTetMesh<double> mesh;
    for (int i = 0; i < nv; ++i) {
        double x,y,z; input >> x >> y >> z;
        mesh.add_vertex(Point3<double>(x,y,z));
    }
    for (int i = 0; i < nt; ++i) {
        int a,b,c,d; input >> a >> b >> c >> d; mesh.add_tet(a,b,c,d);
    }
    mesh.set_fixed_vtx(fixed); mesh.init();
    StVKMaterial material(young*poisson/((1+poisson)*(1-2*poisson)), young/(2*(1+poisson)));
    PardisoMatrix<double> mass, stiffness;
    DeformableFEM::mass_mat(&mesh, mass);
    DeformableFEM::stiffness_mat(&mesh, &material, stiffness);
    output(mass, std::string(argv[2])+".mass.txt");
    output(stiffness, std::string(argv[2])+".stiffness.txt");
}
