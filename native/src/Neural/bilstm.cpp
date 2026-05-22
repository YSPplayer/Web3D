#include "bilstm.h"
#include "math.h"
namespace DeepLr::Neural {
	BiLSTM::BiLSTM():Layer() {
		ntype = NeuralType::BiLSTM;
	}
	Tensor3D BiLSTM::Forward(const Tensor3D& input) { // 1,h,w ->1,h,w
		Tensor3D tensor3D = input;
		Tensor3D c;
		for (int32_t y = 0; y < tensor3D.Height(); ++y) { //时间序列长度
            Tensor3D ft = wf * tensor3D + bf;
			Sigmoid(ft);
			Tensor3D it = wi * tensor3D + bi;
			Sigmoid(it);
			Tensor3D gt = wg * tensor3D + bg;
			Tanh(gt);
			Tensor3D ot = wo * tensor3D + bo;
			Sigmoid(ot);
			c = ft * c + it * gt;
			Tanh(c);
			tensor3D = ot * c;
		}

		return tensor3D;
	}
	void BiLSTM::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
		int32_t h = shape.w;
		int32_t f = lastshape.w;
		wf = Tensor3D(1, h, h + f);
		bf = Tensor3D(1, 1, h);
		wi = Tensor3D(1, h, h + f);
		bi = Tensor3D(1, 1, h);
		wg = Tensor3D(1, h, h + f);
		bg = Tensor3D(1, 1, h);
		wo = Tensor3D(1, h, h + f);
		bo = Tensor3D(1, 1, h);
	}
	void BiLSTM::Sigmoid(Tensor3D& input) {
		const auto& fv = input.Data();
		std::transform(fv.begin(), fv.end(), fv.begin(), [](float x) {
			return DeepLr::Neural::Sigmoid(x);
		});
	}
	void BiLSTM::Tanh(Tensor3D& input) {
		const auto& fv = input.Data();
		std::transform(fv.begin(), fv.end(), fv.begin(), [](float x) {
			return DeepLr::Neural::Tanh(x);
			});
	}
}
