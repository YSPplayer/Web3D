#include "flatten.h"
namespace DeepLr::Neural {
    Flatten::Flatten() :Layer() {
        ntype = NeuralType::Flatten;
    }
    Tensor3D Flatten::Forward(const Tensor3D& input) {
        oldw = input.Width();
        oldh = input.Height();
        oldc = input.Channel();
        int32_t flattenWidth = oldw * oldh * oldc;
        Tensor3D tensor3D = input;
        tensor3D.ReShape(1, 1, flattenWidth);
        return tensor3D;
    }
    Tensor3D Flatten::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
        Tensor3D tensor3D = output;
        tensor3D.ReShape(oldc, oldw, oldh);
        return tensor3D;
    }
}
