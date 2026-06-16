#include "sequencelinear.h"

namespace DeepLr::Neural {
	SequenceLinear::SequenceLinear() : Layer() {
		ntype = NeuralType::SequenceLinear;
		inputSize = 0;
		outputSize = 0;
	}

	void SequenceLinear::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		Layer::SetShape(lastshape, shape);
		inputSize = lastshape.w;
		outputSize = shape.w;
		w = Tensor3D(1, inputSize, outputSize);
		w.HeUniform(inputSize);
		b = Tensor3D(1, 1, outputSize);
		ClearGrad();
	}

	Tensor3D SequenceLinear::Forward(const Tensor3D& input) {
		oldx = input;
		const int32_t T = input.Height();
		Tensor3D output(1, outputSize, T);
		for (int32_t t = 0; t < T; ++t) {
			for (int32_t o = 0; o < outputSize; ++o) {
				float sum = b.Get(0, o, 0);
				for (int32_t f = 0; f < inputSize; ++f) {
					sum += w.Get(0, o, f) * input.Get(0, t, f);
				}
				output.At(0, t, o) = sum;
			}
		}
		return output;
	}

	Tensor3D SequenceLinear::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
		(void)target;
		const int32_t T = output.Height();
		Tensor3D inputGrad(1, inputSize, T);
		for (int32_t t = 0; t < T; ++t) {
			for (int32_t o = 0; o < outputSize; ++o) {
				const float grad = output.Get(0, t, o);
				db.At(0, o, 0) += grad;
				for (int32_t f = 0; f < inputSize; ++f) {
					dw.At(0, o, f) += grad * oldx.Get(0, t, f);
					inputGrad.At(0, t, f) += w.Get(0, o, f) * grad;
				}
			}
		}
		return inputGrad;
	}

	void SequenceLinear::Update(float lr, int32_t batchSize) {
		const float scale = lr / (float)batchSize;
		w = w - dw * scale;
		b = b - db * scale;
		ClearGrad();
	}

	void SequenceLinear::ClearGrad() {
		dw = Tensor3D(1, inputSize, outputSize);
		db = Tensor3D(1, 1, outputSize);
	}

	void SequenceLinear::AccumulateGrad(const Layer& other) {
		const SequenceLinear* sequenceLinear = dynamic_cast<const SequenceLinear*>(&other);
		if (!sequenceLinear) return;
		dw = dw + sequenceLinear->dw;
		db = db + sequenceLinear->db;
	}

	Tensor3D SequenceLinear::GetW() const {
		return w;
	}

	Tensor3D SequenceLinear::GetB() const {
		return b;
	}

	void SequenceLinear::SetW(const Tensor3D& w) {
		this->w = w;
	}

	void SequenceLinear::SetB(const Tensor3D& b) {
		this->b = b;
	}
}
