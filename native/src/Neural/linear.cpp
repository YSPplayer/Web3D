#include "linear.h"
#include "../log.h"
#include <format>
namespace DeepLr::Neural {
    Linear::Linear():Layer() {
        ntype = NeuralType::Linear;
    }
    void Linear::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
        Layer::SetShape(lastshape, shape);
        int32_t inputSize = lastshape.c * lastshape.w * lastshape.h;
        int32_t outputSize = shape.c * shape.w * shape.h;
        w = Tensor3D(1, inputSize, outputSize);
        w.HeUniform(inputSize);
        b = Tensor3D(1, 1, outputSize);
        dw  = Tensor3D(1, inputSize, outputSize);
        db = Tensor3D(1, 1, outputSize);
    }
    Tensor3D Linear::Forward(const Tensor3D& input) {
        this->oldx = input;
        this->oldy = w * input + b;
        return this->oldy;
    }
    Tensor3D Linear::Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) {
        Tensor3D temp = output;
        temp.ReShape(1,1, output.Shape());//shape (40,1)
        Tensor3D tempw(this->w); //y = wx + b -> y = w
        tempw.Transpose();
        Tensor3D tempOldx = this->oldx;
        tempOldx.Transpose();
        //´æ´¢WºÍB
        this->dw = dw + temp * tempOldx;
        this->db = db + temp;
        return tempw * temp;
    }
    void Linear::Update(float lr, int32_t batchSize) {
        float oldW0 = w.Count() > 0 ? w.At(0) : 0.0f;
        float oldB0 = b.Count() > 0 ? b.At(0) : 0.0f;
        float dwAbs = dw.SumAbs();
        float dbAbs = db.SumAbs();
        w = w - dw * (lr / (float)batchSize);
        b = b - db * (lr / (float)batchSize);
        if (batchSize <= 8) {
            float newW0 = w.Count() > 0 ? w.At(0) : 0.0f;
            float newB0 = b.Count() > 0 ? b.At(0) : 0.0f;
            Log::Debug(std::format(
                "debug Linear update in={},out={},batch={},dwAbs={},dbAbs={},w0Before={},w0After={},b0Before={},b0After={}",
                lastshape.c * lastshape.w * lastshape.h, shape.c * shape.w * shape.h, batchSize, dwAbs, dbAbs, oldW0, newW0, oldB0, newB0));
        }
        dw = Tensor3D(1, lastshape.c * lastshape.w * lastshape.h, shape.c * shape.w * shape.h);
        db = Tensor3D(1, 1, shape.c * shape.w * shape.h);
    }
    void Linear::ClearGrad() {
        dw = Tensor3D(1, lastshape.c * lastshape.w * lastshape.h, shape.c * shape.w * shape.h);
        db = Tensor3D(1, 1, shape.c * shape.w * shape.h);
    }
    void Linear::AccumulateGrad(const Layer& other) {
        const Linear* linear = dynamic_cast<const Linear*>(&other);
        if (!linear) return;
        dw = dw + linear->dw;
        db = db + linear->db;
    }
    void Linear::SetW(const Tensor3D& w) {
        this->w = w;
    }
    void Linear::SetB(const Tensor3D& b) {
        this->b = b;
    }
}