#include "maxpool.h"
#include <limits>
namespace DeepLr::Neural {
	MaxPool::MaxPool():Layer() {
		ntype = NeuralType::MaxPool;
		poolH = 2;
		poolW = 2;
	}
	void MaxPool::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
		poolH = shape.h > 0 ? std::max(1, lastshape.h / shape.h) : 2;
		poolW = shape.w > 0 ? std::max(1, lastshape.w / shape.w) : 2;
	}
	Tensor3D MaxPool::Forward(const Tensor3D& input) {
		Tensor3D tensor3D(input.Channel(), input.Width() / poolW, input.Height() / poolH);
		int32_t c = input.Channel();
		int32_t outH = tensor3D.Height();
		int32_t outW = tensor3D.Width();
		indexs.clear();
		indexs.resize(c);
		for (int32_t i = 0; i < c; ++i) {
			indexs[i].reserve(outW * outH);
			for (int32_t y = 0; y < outH; ++y) {
				for (int32_t x = 0; x < outW; ++x) {
					float maxvalue = std::numeric_limits<float>::lowest();
					Point2D maxpoint{ x * poolW, y * poolH };
					for (int32_t py = 0; py < poolH; ++py) {
						for (int32_t px = 0; px < poolW; ++px) {
							int32_t inputY = y * poolH + py;
							int32_t inputX = x * poolW + px;
							float value = input.Get(i, inputY, inputX);
							if (value > maxvalue) {
								maxvalue = value;
								maxpoint = { inputX, inputY };
							}
						}
					}
					indexs[i].push_back(maxpoint);
					tensor3D.At(i, y, x) = maxvalue;
				}
			}
		}
		return tensor3D;
	}
	Tensor3D MaxPool::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		Tensor3D tensor3D(lastshape.c, lastshape.w, lastshape.h);
		int32_t c = output.Channel();
		int32_t w = output.Width();
		for (int32_t i = 0; i < c; ++i) {
			for (int32_t j = 0; j < indexs[i].size(); ++j) {
				const Point2D& point = indexs[i][j];
				tensor3D.At(i, point.y, point.x) += output.Get(i, j / w, j % w);
			}
		}
		return tensor3D;
	}
}
