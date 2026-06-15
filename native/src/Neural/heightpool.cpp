#include <limits>
#include "heightpool.h"
namespace DeepLr::Neural {
	HeightPool::HeightPool():Layer() {
		ntype = NeuralType::HeightPool;
	}

	Tensor3D HeightPool::Forward(const Tensor3D& input) { // c h w -> c 1 w
		Tensor3D tensor3D(input.Channel(), input.Width(),1);
		maxindex.clear();
		maxindex.resize(input.Channel());
		for (int32_t i = 0; i < maxindex.size(); ++i) {
			maxindex[i].resize(input.Width());
		}
		for (int32_t c = 0; c < input.Channel(); ++c) {
			for (int32_t x = 0; x < input.Width(); ++x) {
				float maxvalue = std::numeric_limits<float>::lowest();
				float tempvalue = maxvalue;
				for (int32_t y = 0; y < input.Height(); ++y) {
					tempvalue = std::max(maxvalue, input.Get(c,y,x));
					if (tempvalue != maxvalue) maxindex[c][x] = y;
					maxvalue = tempvalue;
				}
				tensor3D.At(c, 0, x) = maxvalue;
			}
		}
		return tensor3D;
	}

	Tensor3D HeightPool::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) { //c 1 w ->  c h w
		Tensor3D tensor3D(lastshape.c, lastshape.w, lastshape.h);
		for (int32_t c = 0; c < output.Channel(); ++c) {
			for (int32_t x = 0; x < output.Width(); ++x) {
				int32_t index = maxindex[c][x];
				tensor3D.At(c, index, x) = output.At(c,0,x);
			}
		}
		return tensor3D;
	}

	void HeightPool::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
	}

}