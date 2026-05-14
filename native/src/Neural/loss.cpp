#include "loss.h"
#include <cmath>
namespace DeepLr::Neural {
    float Loss::Forward(const Tensor3D& input) {
        float sum = 0.0;
        float eps = 1e-7;
        for (int32_t i = 0; i < target.size(); ++i) {
            float value = input.Get(0, i, target[i]);
            sum += (-log(std::max(value, eps)));
        }
        return sum / (float)target.size();
    }
}
