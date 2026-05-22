#include "heightpool.h"
namespace DeepLr::Neural {
	HeightPool::HeightPool():Layer() {
		ntype = NeuralType::HeightPool;
	}

	Tensor3D HeightPool::Forward(const Tensor3D& input) { // c h w -> c 1 w
		Tensor3D tensor3D(input.Channel(), input.Width(),1);
		for (int32_t c = 0; c < input.Channel(); ++c) {
			for (int32_t x = 0; x < input.Width(); ++x) {
				float maxvalue = std::numeric_limits<float>::lowest();
				for (int32_t y = 0; y < input.Height(); ++y) {
					maxvalue = std::max(maxvalue, input.Get(c,y,x));
				}
				tensor3D.At(c, 0, x) = maxvalue;
			}
		}
		return tensor3D;
	}

}