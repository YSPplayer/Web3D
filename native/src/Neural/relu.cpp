#include <algorithm>
#include "relu.h"
namespace DeepLr::Neural {
	Tensor3D Relu::Forward(const Tensor3D& input) {
		Tensor3D tensor3D(input.Channel(), input.Width(), input.Height());
		for (int32_t i = 0; i < tensor3D.Count(); ++i) {
			tensor3D.At(i) = std::max(0.0f, input.Get(i));
		}
		return tensor3D;
	}
}
