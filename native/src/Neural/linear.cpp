#include "linear.h"
namespace DeepLr::Neural {
    Linear::Linear(int32_t lasth, int32_t h):lasth(lasth), h(h){
        ntype = NeuralType::Linear;
        w = Tensor3D(1, lasth, h);
        w.HeUniform(lasth);
        b = Tensor3D(1, 1, h);
    }
    Tensor3D Linear::Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) {
        this->oldx = input;
        this->oldy = w * input + b;
        return this->oldy;
    }
    Tensor3D Linear::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
        Tensor3D temp = output;
        temp.ReShape(1,1, output.Shape());//shape (40,1)
        Tensor3D tempw(this->w); //y = wx + b -> y = w
        tempw.Transpose();
        Tensor3D tempOldx = this->oldx;
        tempOldx.Transpose();
        //´æ´¢WºÍB
        this->dw = temp * tempOldx;
        this->db = temp;
        return tempw * temp;
    }
}