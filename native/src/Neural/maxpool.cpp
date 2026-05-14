#include "maxpool.h"
namespace DeepLr::Neural {
	MaxPool::MaxPool():Layer() {
		ntype = NeuralType::MaxPool;
	}
	Tensor3D MaxPool::Forward(const Tensor3D& input) {
		Tensor3D tensor3D(input.Channel(), input.Width() / 2, input.Height() / 2);
		int32_t c = input.Channel();
		int32_t h = input.Height();
		int32_t w = input.Width();
		int32_t index = 0;
		indexs.clear();
		indexs.resize(tensor3D.Channel());
		for (int32_t i = 0; i < c; ++i) {
			indexs[i].reserve(tensor3D.Width() * tensor3D.Height());
			for (int32_t y = 0; y < h; y+=2) {
				for (int32_t x = 0; x < w; x+=2) {
					float value1 = input.Get(i,y,x);
					float value2 = input.Get(i, y, x + 1);
					float value3 = input.Get(i, y + 1, x);
					float value4 = input.Get(i, y + 1, x + 1);
					float maxvalue = std::max({ value1, value2, value3, value4 });
					if (maxvalue == value1) indexs[i].push_back({ x,y });
					else if(maxvalue == value2) indexs[i].push_back({ x + 1 ,y});
					else if (maxvalue == value3) indexs[i].push_back({ x, y + 1 });
					else  indexs[i].push_back({ x + 1,y + 1 });
					tensor3D.At(index++) = maxvalue;
				}
			}
		}
		return tensor3D;
	}
	Tensor3D MaxPool::Backward(const Tensor3D& output) {
		Tensor3D tensor3D(output.Channel(), output.Width() * 2, output.Height() * 2);
		int32_t c = output.Channel();
		int32_t h = output.Height();
		int32_t w = output.Width();
		for (int32_t i = 0; i < c; ++i) {
			for (int32_t j = 0; j < indexs[i].size(); ++j) {
				const Point2D& point = indexs[i][j];
				tensor3D.At(i, point.y, point.x) = output.At(i * indexs[i].size() + j);
			}
		}
		return tensor3D;
	}
}