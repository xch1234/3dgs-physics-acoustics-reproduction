// Calls the unmodified educational transfer integrator and multipole code.
#include <iostream>
#include <iomanip>
#include <fstream>
#include "generic/precision_type.hpp"
#include "transfer/FMMBoundIntTransfer.hpp"

int main(int argc,char** argv) {
    if(argc!=5) return 2;
    BoundaryIntegralTransfer<double> direct(argv[1],argv[2]);
    FMMBoundIntTransfer<double> multipole(argv[1],argv[2]);
    multipole.compute_moments();
    const std::string prefix(argv[4]);
    multipole.store_moments((prefix+"_moments.ma").c_str());
    std::ofstream moments(prefix+"_moments.txt");
    moments<<std::setprecision(17);
    for(const auto& c:multipole.moments()) moments<<c.real()<<" "<<c.imag()<<"\n";
    std::ifstream points(argv[3]);std::ofstream output(prefix+"_field.txt");
    output<<std::setprecision(17);
    double x,y,z;
    while(points>>x>>y>>z) {
        Point3<double> p(x,y,z);
        auto a=direct.eval(p),b=multipole.eval(p);
        output<<x<<" "<<y<<" "<<z<<" "<<a.real()<<" "<<a.imag()<<" "<<b.real()<<" "<<b.imag()<<"\n";
    }
    std::ofstream meta(prefix+"_meta.txt");
    meta<<multipole.num_elements()<<" "<<multipole.expansion_num()<<"\n";
    return output.good() && moments.good()?0:3;
}
