#include "flatten.h"
namespace DeepLr::Neural {
    Tensor3D Flatten::Forward(const Tensor3D& input) {
        int32_t w = input.Width();
        int32_t h = input.Height();
        int32_t c = input.Channel();
        int32_t flattenWidth = w * h * c;
        Tensor3D tensor3D = input;
        tensor3D.ReShape(1, 1, flattenWidth);
        return tensor3D;
    }
}
