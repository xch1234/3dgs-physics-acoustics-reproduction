// Evaluate the unchanged educational ModalSound basis and its analytic gradient.
#include <iostream>
#include <iomanip>
#include "transfer/HelmholtzBasis.hpp"

static Point3<double> spherical(const Point3<double>& p) {
    double r=std::sqrt(p.x*p.x+p.y*p.y+p.z*p.z);
    return Point3<double>(r,std::acos(p.z/r),std::atan2(p.y,p.x));
}
int main() {
    std::cout << std::setprecision(17);
    const Vector3<double> dir(.3,-.4,.5);
    for(int j=0;j<24;++j) {
        Point3<double> p(.03+.007*j,.08*std::sin(j*.71)+.013,.05*std::cos(j*.39)+.009);
        double k=3.+2.*j,h=1e-6;
        auto sc=spherical(p);
        for(int n=0;n<6;++n)for(int m=-n;m<=n;++m) {
            auto s=HelmholtzBasis::singular_basis(m,n,k,sc);
            auto d=HelmholtzBasis::regular_basis_dir_deriv(m,n,k,sc,dir);
            auto a=HelmholtzBasis::regular_basis(m,n,k,spherical(Point3<double>(p.x+h*dir.x,p.y+h*dir.y,p.z+h*dir.z)));
            auto b=HelmholtzBasis::regular_basis(m,n,k,spherical(Point3<double>(p.x-h*dir.x,p.y-h*dir.y,p.z-h*dir.z)));
            auto fd=(a-b)/(2*h);
            std::cout<<j<<' '<<n<<' '<<m<<' '<<k<<' '<<sc.r<<' '<<sc.theta<<' '<<sc.phi<<' '
                     <<s.real()<<' '<<s.imag()<<' '<<d.real()<<' '<<d.imag()<<' '<<fd.real()<<' '<<fd.imag()<<'\n';
        }
    }
}
